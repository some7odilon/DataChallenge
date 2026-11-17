import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DataMetadata, RegionData, RegionalDataService } from '../../data/regional-data.service';

type PriorityFilter = 'tous' | 'prioritaire' | 'à surveiller' | 'moins exposée';

@Component({
  selector: 'app-dashboard-page',
  imports: [RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardPage implements OnInit {
  private readonly regionalData = inject(RegionalDataService);

  readonly regions = signal<RegionData[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly activeFilter = signal<PriorityFilter>('tous');
  readonly search = signal('');
  readonly selectedCode = signal('');
  readonly metadata = signal<DataMetadata | null>(null);
  readonly referenceYear = signal('2024/25');

  readonly selectedRegion = computed(
    () => this.regions().find((region) => region.code === this.selectedCode()) ?? this.regions()[0],
  );
  readonly filteredRegions = computed(() => {
    const filter = this.activeFilter();
    const query = this.search().trim().toLocaleLowerCase('fr');
    return this.regions()
      .filter((region) => filter === 'tous' || region.niveau.toLocaleLowerCase('fr') === filter)
      .filter((region) => !query || region.region.toLocaleLowerCase('fr').includes(query) || region.code.toLocaleLowerCase('fr').includes(query));
  });
  readonly priorityCount = computed(() => this.regions().filter((region) => region.niveau === 'prioritaire').length);
  readonly watchCount = computed(() => this.regions().filter((region) => region.niveau === 'à surveiller').length);
  readonly lowestScore = computed(() => this.regions().reduce((lowest, region) => Math.min(lowest, region.score), 100));
  readonly highestScore = computed(() => this.regions().reduce((highest, region) => Math.max(highest, region.score), 0));

  ngOnInit(): void {
    this.regionalData.load().subscribe({
      next: (data) => {
        const regions = this.regionalData.toRegions(data);
        this.regions.set(regions);
        this.selectedCode.set(regions[0]?.code ?? '');
        this.metadata.set(data.metadata);
        this.referenceYear.set(this.regionalData.referenceYear(data));
        this.loading.set(false);
      },
      error: () => {
        this.loadError.set(true);
        this.loading.set(false);
      },
    });
  }

  selectFilter(filter: PriorityFilter): void {
    this.activeFilter.set(filter);
  }

  selectRegion(region: RegionData): void {
    this.selectedCode.set(region.code);
  }

  formatScore(score: number | undefined): string {
    return score === undefined ? '—' : score.toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }

  formatPercent(value: number | undefined): string {
    return value === undefined ? '—' : `${value.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`;
  }

  getTrendPoints(completion: Record<string, number> | undefined): string {
    if (!completion) return '';
    const values = Object.entries(completion).sort(([a], [b]) => Number(a) - Number(b)).map(([, value]) => value);
    const min = Math.min(...values);
    const range = Math.max(...values) - min || 1;
    return values.map((value, index) => `${(index / Math.max(values.length - 1, 1)) * 280},${92 - ((value - min) / range) * 72}`).join(' ');
  }

  getTrendEndY(completion: Record<string, number> | undefined): number {
    const lastPoint = this.getTrendPoints(completion).split(' ').at(-1);
    return Number(lastPoint?.split(',')[1] ?? 92);
  }

  indicatorLabel(key: string): string {
    const labels: Record<string, string> = {
      achevement_niveau: 'Achèvement primaire',
      achevement_tendance: 'Évolution de l’achèvement',
      ecart_genre_achevement: 'Écart filles-garçons',
      reussite_cep: 'Réussite au CEP',
      choc_ecoles_effectifs: 'Pression sur les écoles',
      entrees_cp1: 'Entrées au CP1',
      scolarisation_tbs: 'Scolarisation au primaire',
      presco_acces: 'Accès au préscolaire',
    };
    return labels[key] ?? key.replaceAll('_', ' ');
  }

  indicatorRisk(region: RegionData, key: string): number {
    return Math.max(0, Math.min(100, region.indicators?.[key]?.risque ?? 0));
  }

  generatedDate(): string {
    const generated = this.metadata()?.genere_le;
    if (!generated) return '—';
    return new Date(`${generated}T00:00:00`).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  get completionYears(): string[] {
    const years = Object.keys(this.selectedRegion()?.completion ?? {}).sort();
    return years.length ? years.filter((_, index) => index === 0 || index === years.length - 1) : ['2015', '2024'];
  }
}
