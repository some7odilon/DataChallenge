import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DataMetadata, RegionData, RegionalDataService } from '../../data/regional-data.service';

interface ComparisonEntry {
  region: RegionData;
  value: number | null;
  risk: number | null;
}

interface ComparisonMetric {
  code: string;
  label: string;
  note?: string;
  entries: ComparisonEntry[];
  spread: number | null;
}

@Component({
  selector: 'app-compare-regions-page',
  imports: [RouterLink],
  templateUrl: './compare-regions.html',
  styleUrl: './compare-regions.css',
})
export class CompareRegionsPage implements OnInit {
  private readonly regionalData = inject(RegionalDataService);

  readonly regions = signal<RegionData[]>([]);
  readonly metadata = signal<DataMetadata | null>(null);
  readonly referenceYear = signal('2024/25');
  readonly selectedCodes = signal<string[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal(false);

  readonly selectedRegions = computed(() => this.selectedCodes()
    .map((code) => this.regions().find((region) => region.code === code))
    .filter((region): region is RegionData => region !== undefined));
  readonly indicators = computed<ComparisonMetric[]>(() => {
    const selected = this.selectedRegions();
    const definitions = this.metadata()?.indicateurs ?? {};
    return Object.keys(definitions).map((code) => {
      const entries = selected.map((region) => ({
        region,
        value: region.indicators?.[code]?.valeur ?? null,
        risk: region.indicators?.[code]?.risque ?? null,
      }));
      const risks = entries.flatMap((entry) => entry.risk === null ? [] : [entry.risk]);
      return {
        code,
        label: definitions[code]?.label ?? this.humanize(code),
        note: definitions[code]?.note,
        entries,
        spread: risks.length > 1 ? Math.max(...risks) - Math.min(...risks) : null,
      };
    });
  });
  readonly largestGap = computed(() => this.indicators()
    .filter((metric) => metric.spread !== null)
    .sort((a, b) => (b.spread ?? 0) - (a.spread ?? 0))[0]);
  readonly completionYears = computed(() => Object.keys(this.selectedRegions()[0]?.completionByGender?.T ?? {}).sort());
  readonly priorityCount = computed(() => this.selectedRegions().filter((region) => region.niveau === 'prioritaire').length);
  readonly referenceCount = computed(() => this.selectedRegions().filter((region) => region.niveau === 'moins exposée').length);

  ngOnInit(): void {
    this.regionalData.load().subscribe({
      next: (data) => {
        const regions = this.regionalData.toRegions(data);
        this.regions.set(regions);
        this.metadata.set(data.metadata);
        this.referenceYear.set(this.regionalData.referenceYear(data));
        const priority = regions.filter((region) => region.niveau === 'prioritaire');
        const leastExposed = [...regions].reverse().find((region) => region.niveau === 'moins exposée');
        const defaults = [priority[0]?.code, priority[1]?.code, leastExposed?.code].filter((code): code is string => !!code);
        this.selectedCodes.set([...new Set(defaults)].slice(0, 3));
        this.loading.set(false);
      },
      error: () => {
        this.loadError.set(true);
        this.loading.set(false);
      },
    });
  }

  addRegion(): void {
    const current = this.selectedCodes();
    const next = this.regions().find((region) => !current.includes(region.code));
    if (current.length < 3 && next) this.selectedCodes.set([...current, next.code]);
  }

  removeRegion(index: number): void {
    const current = this.selectedCodes();
    if (current.length <= 2) return;
    this.selectedCodes.set(current.filter((_, currentIndex) => currentIndex !== index));
  }

  selectRegion(index: number, code: string): void {
    const current = this.selectedCodes();
    if (current.some((selected, currentIndex) => currentIndex !== index && selected === code)) return;
    this.selectedCodes.set(current.map((selected, currentIndex) => currentIndex === index ? code : selected));
  }

  reset(): void {
    const priority = this.regions().filter((region) => region.niveau === 'prioritaire');
    const leastExposed = [...this.regions()].reverse().find((region) => region.niveau === 'moins exposée');
    this.selectedCodes.set([...new Set([priority[0]?.code, priority[1]?.code, leastExposed?.code].filter((code): code is string => !!code))].slice(0, 3));
  }

  formatScore(value: number | null | undefined): string {
    return value === null || value === undefined ? '—' : value.toLocaleString('fr-FR', { maximumFractionDigits: 1 });
  }

  formatValue(value: number | null): string {
    return value === null ? 'Donnée indisponible' : value.toLocaleString('fr-FR', { maximumFractionDigits: 2 });
  }

  formatScoreInterval(region: RegionData): string {
    return `${this.formatScore(region.rang_p5)} — ${this.formatScore(region.rang_p95)}`;
  }

  statusClass(region: RegionData): string {
    return region.niveau === 'prioritaire' ? 'priority' : region.niveau === 'à surveiller' ? 'watch' : 'lower';
  }

  humanize(code: string): string {
    const labels: Record<string, string> = {
      achevement_niveau: 'Achèvement primaire récent',
      achevement_tendance: 'Évolution de l’achèvement',
      ecart_genre_achevement: 'Écart filles-garçons d’achèvement',
      reussite_cep: 'Réussite au CEP',
      choc_ecoles_effectifs: 'Perturbation des écoles et effectifs',
      entrees_cp1: 'Évolution des entrées au CP1',
      scolarisation_tbs: 'Scolarisation au primaire',
      presco_acces: 'Accès au préscolaire',
    };
    return labels[code] ?? code.replaceAll('_', ' ');
  }

  getSeriesPoints(region: RegionData): string {
    const years = this.completionYears();
    const series = region.completionByGender?.T;
    if (!years.length || !series) return '';
    return years.map((year, index) => {
      const x = 60 + index * (880 / Math.max(years.length - 1, 1));
      const value = Math.max(0, Math.min(100, series[year] ?? 0));
      const y = 290 - (value / 100) * 260;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }

  getShockX(): number {
    const shockYear = String(this.metadata()?.annee_choc ?? '').split('/')[0];
    const index = this.completionYears().indexOf(shockYear);
    return 60 + (index < 0 ? 7 : index) * (880 / Math.max(this.completionYears().length - 1, 1));
  }

  shockYearLabel(): string {
    const value = this.metadata()?.annee_choc;
    if (!value) return '—';
    const year = Number(String(value).split('/')[0]);
    return Number.isFinite(year) ? `${year}/${String(year + 1).slice(-2)}` : String(value);
  }

  printComparison(): void {
    window.print();
  }
}
