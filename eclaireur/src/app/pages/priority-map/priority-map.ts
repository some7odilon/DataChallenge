import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DataMetadata, RegionData, RegionalDataService } from '../../data/regional-data.service';

type PriorityFilter = 'tous' | 'prioritaire' | 'à surveiller' | 'moins exposée';

interface MapRegion {
  code: string;
  points: string;
  x: number;
  y: number;
}

@Component({
  selector: 'app-priority-map-page',
  imports: [RouterLink],
  templateUrl: './priority-map.html',
  styleUrl: './priority-map.css',
})
export class PriorityMapPage implements OnInit {
  private readonly regionalData = inject(RegionalDataService);
  private readonly route = inject(ActivatedRoute);

  readonly regions = signal<RegionData[]>([]);
  readonly metadata = signal<DataMetadata | null>(null);
  readonly referenceYear = signal('2024/25');
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly selectedCode = signal('');
  readonly activeFilter = signal<PriorityFilter>('tous');

  readonly selectedRegion = computed(
    () => this.regions().find((region) => region.code === this.selectedCode()) ?? this.regions()[0],
  );
  readonly visibleRegions = computed(() => {
    const filter = this.activeFilter();
    return this.regions().filter((region) => filter === 'tous' || region.niveau === filter);
  });
  readonly visibleCodes = computed(() => new Set(this.visibleRegions().map((region) => region.code)));
  readonly priorityCount = computed(() => this.regions().filter((region) => region.niveau === 'prioritaire').length);
  readonly watchCount = computed(() => this.regions().filter((region) => region.niveau === 'à surveiller').length);
  readonly lowerCount = computed(() => this.regions().filter((region) => region.niveau === 'moins exposée').length);

  readonly mapLayout: MapRegion[] = [
    { code: 'SAH', points: '510,40 680,25 760,110 740,195 620,185 540,145 490,120 480,75', x: 615, y: 108 },
    { code: 'NOR', points: '340,130 480,120 495,190 410,225 350,220 305,170', x: 409, y: 177 },
    { code: 'CNO', points: '495,125 545,148 620,190 600,280 500,280 475,220', x: 545, y: 218 },
    { code: 'EST', points: '625,195 745,200 890,265 890,390 770,440 680,360 635,280', x: 755, y: 318 },
    { code: 'BMH', points: '210,180 340,135 348,220 300,270 330,360 250,380 180,310 185,230', x: 257, y: 278 },
    { code: 'PCL', points: '465,235 520,230 550,285 500,325 440,310 445,260', x: 500, y: 280 },
    { code: 'CEN', points: '445,295 480,295 485,335 440,335', x: 462, y: 320 },
    { code: 'COU', points: '310,270 435,260 440,350 370,410 320,360', x: 377, y: 340 },
    { code: 'CSU', points: '445,340 500,330 520,430 450,435 435,395', x: 486, y: 390 },
    { code: 'CES', points: '535,290 630,285 665,370 595,445 525,415 520,335', x: 594, y: 362 },
    { code: 'HBS', points: '120,330 240,360 270,450 170,510 115,440', x: 183, y: 430 },
    { code: 'CAS', points: '80,450 170,510 175,595 70,570 50,490', x: 124, y: 537 },
    { code: 'SOU', points: '175,510 270,455 330,470 330,575 220,590 180,570', x: 254, y: 532 },
  ];

  ngOnInit(): void {
    const requestedCode = this.route.snapshot.queryParamMap.get('region')?.toUpperCase();
    this.regionalData.load().subscribe({
      next: (data) => {
        const regions = this.regionalData.toRegions(data);
        this.regions.set(regions);
        this.metadata.set(data.metadata);
        this.referenceYear.set(this.regionalData.referenceYear(data));
        this.selectedCode.set(regions.find((region) => region.code === requestedCode)?.code ?? regions[0]?.code ?? '');
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
    const firstVisible = this.regions().find((region) => filter === 'tous' || region.niveau === filter);
    if (firstVisible) this.selectedCode.set(firstVisible.code);
  }

  selectRegion(region: RegionData): void {
    this.selectedCode.set(region.code);
  }

  regionForCode(code: string): RegionData | undefined {
    return this.regions().find((region) => region.code === code);
  }

  regionClass(region: RegionData): string {
    return region.niveau === 'prioritaire' ? 'map-priority' : region.niveau === 'à surveiller' ? 'map-watch' : 'map-lower';
  }

  formatScore(score: number | undefined): string {
    return score === undefined ? '—' : score.toLocaleString('fr-FR', { maximumFractionDigits: 1 });
  }

  formatProbability(probability: number): string {
    return `${Math.round(probability * 100)} %`;
  }

  indicatorLabel(key: string): string {
    const labels: Record<string, string> = {
      achevement_niveau: 'Achèvement primaire',
      achevement_tendance: 'Évolution de l’achèvement',
      ecart_genre_achevement: 'Écart filles-garçons',
      reussite_cep: 'Réussite au CEP',
      choc_ecoles_effectifs: 'Pression sur les écoles',
      entrees_cp1: 'Entrées au CP1',
      scolarisation_tbs: 'Scolarisation primaire',
      presco_acces: 'Accès au préscolaire',
    };
    return labels[key] ?? key.replaceAll('_', ' ');
  }

  indicatorRisk(region: RegionData, key: string): number {
    return Math.max(0, Math.min(100, region.indicators?.[key]?.risque ?? 0));
  }

  get probabilityPercent(): number {
    return Math.round((this.selectedRegion()?.prob_prioritaire ?? 0) * 100);
  }

  get activeFactors(): string[] {
    return (this.selectedRegion()?.profile?.facteurs_dominants ?? []).slice(0, 3);
  }
}
