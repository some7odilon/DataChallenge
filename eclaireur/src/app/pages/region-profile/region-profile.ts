import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { DataMetadata, RegionData, RegionalDataService } from '../../data/regional-data.service';

interface FactorRow {
  code: string;
  contribution: number;
  risk: number | null;
  weight: number;
}

@Component({
  selector: 'app-region-profile-page',
  imports: [RouterLink],
  templateUrl: './region-profile.html',
  styleUrl: './region-profile.css',
})
export class RegionProfilePage implements OnInit {
  private readonly regionalData = inject(RegionalDataService);
  private readonly route = inject(ActivatedRoute);

  readonly regions = signal<RegionData[]>([]);
  readonly metadata = signal<DataMetadata | null>(null);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly selectedCode = signal('');
  readonly referenceYear = signal('2024/25');

  readonly selectedRegion = computed(
    () => this.regions().find((region) => region.code === this.selectedCode()) ?? this.regions()[0],
  );
  readonly factors = computed<FactorRow[]>(() => {
    const region = this.selectedRegion();
    if (!region) return [];
    return Object.entries(region.profile?.contributions ?? {})
      .map(([code, contribution]) => ({
        code,
        contribution,
        risk: region.indicators?.[code]?.risque ?? null,
        weight: this.metadata()?.ponderations?.[code] ?? 0,
      }))
      .sort((a, b) => b.contribution - a.contribution)
      .slice(0, 3);
  });
  readonly indicatorRows = computed(() => {
    const region = this.selectedRegion();
    if (!region) return [];
    const order = Object.keys(this.metadata()?.indicateurs ?? {});
    return order.map((code) => ({ code, ...region.indicators?.[code] }));
  });
  readonly completionYears = computed(() => Object.keys(this.selectedRegion()?.completionByGender?.T ?? {}).sort());
  readonly comparisonSeries = computed(() => [
    { code: 'T', label: 'Total régional', cssClass: 'series-total' },
    { code: 'G', label: 'Garçons', cssClass: 'series-boys' },
    { code: 'F', label: 'Filles', cssClass: 'series-girls' },
  ] as const);

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const code = params.get('region');
      if (code) this.selectedCode.set(code.toUpperCase());
    });
    this.regionalData.load().subscribe({
      next: (data) => {
        const regions = this.regionalData.toRegions(data);
        this.regions.set(regions);
        this.metadata.set(data.metadata);
        this.referenceYear.set(this.regionalData.referenceYear(data));
        if (!this.selectedCode() || !regions.some((region) => region.code === this.selectedCode())) {
          this.selectedCode.set(regions[0]?.code ?? '');
        }
        this.loading.set(false);
      },
      error: () => {
        this.loadError.set(true);
        this.loading.set(false);
      },
    });
  }

  selectRegion(code: string): void {
    this.selectedCode.set(code);
  }

  rankSuffix(rank: number): string {
    return rank === 1 ? 'er' : 'e';
  }

  formatScore(value: number | null | undefined): string {
    return value === null || value === undefined ? '—' : value.toLocaleString('fr-FR', { maximumFractionDigits: 1 });
  }

  formatPercent(value: number | undefined): string {
    return value === undefined ? '—' : `${(value * 100).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} %`;
  }

  formatRaw(value: number | null | undefined): string {
    return value === null || value === undefined ? 'Non renseigné' : value.toLocaleString('fr-FR', { maximumFractionDigits: 2 });
  }

  indicatorLabel(code: string): string {
    return this.metadata()?.indicateurs?.[code]?.label ?? this.humanize(code);
  }

  humanize(code: string): string {
    const labels: Record<string, string> = {
      achevement_niveau: 'Achèvement primaire récent',
      achevement_tendance: 'Évolution de l’achèvement',
      ecart_genre_achevement: 'Écart filles-garçons',
      reussite_cep: 'Réussite au CEP',
      choc_ecoles_effectifs: 'Perturbation des écoles et effectifs',
      entrees_cp1: 'Évolution des entrées au CP1',
      scolarisation_tbs: 'Scolarisation au primaire',
      presco_acces: 'Accès au préscolaire',
    };
    return labels[code] ?? code.replaceAll('_', ' ');
  }

  sourceLabel(code: string): string {
    const labels: Record<string, string> = {
      primaire_achevement_region: 'Achèvement primaire',
      primaire_tbs_region: 'Scolarisation primaire',
      primaire_cep_region: 'Résultats CEP',
      primaire_nouveaux_cp1_region: 'Entrées au CP1',
      primaire_effectifs_region: 'Effectifs scolaires',
      primaire_ecoles_region: 'Écoles primaires',
      prescolaire_T5: 'Préscolaire',
    };
    return labels[code] ?? code.replaceAll('_', ' ');
  }

  sourceLabels(codes: string[] | undefined): string {
    return codes?.map((code) => this.sourceLabel(code)).join(', ') || 'Source non précisée';
  }

  getSeriesPoints(seriesCode: 'T' | 'G' | 'F'): string {
    const years = this.completionYears();
    const series = this.selectedRegion()?.completionByGender?.[seriesCode];
    if (!years.length || !series) return '';
    return years.map((year, index) => {
      const x = 36 + index * (350 / Math.max(years.length - 1, 1));
      const value = Math.max(0, Math.min(100, series[year] ?? 0));
      const y = 188 - (value / 100) * 165;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }

  getShockX(): number {
    const year = Number(String(this.metadata()?.annee_choc ?? '').split('/')[0]);
    const index = this.completionYears().indexOf(String(year));
    if (index < 0) return 36 + (5 * 350) / 9;
    return 36 + index * (350 / Math.max(this.completionYears().length - 1, 1));
  }

  shockYearLabel(): string {
    const yearValue = this.metadata()?.annee_choc;
    if (!yearValue) return '—';
    const year = Number(String(yearValue).split('/')[0]);
    return Number.isFinite(year) ? `${year}/${String(year + 1).slice(-2)}` : String(yearValue);
  }

  indicatorCount(): number {
    return this.indicatorRows().filter((row) => row.valeur !== null && row.valeur !== undefined).length;
  }

  printPage(): void {
    window.print();
  }
}
