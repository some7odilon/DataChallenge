import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { forkJoin, Observable, shareReplay } from 'rxjs';

export interface RegionScore {
  code: string;
  region: string;
  score: number;
  rang: number;
  rang_p5: number;
  rang_p95: number;
  niveau: string;
  confiance: string;
  classement_robuste: boolean;
  prob_prioritaire: number;
}

export interface RegionProfile {
  code: string;
  profil: string;
  recommandation: string;
  facteurs_dominants: string[];
  groupe_en_retrait: string | null;
  contributions: Record<string, number>;
}

export interface RegionIndicator {
  valeur: number;
  risque: number | null;
}

export interface RegionData extends RegionScore {
  profile?: RegionProfile;
  indicators?: Record<string, RegionIndicator>;
  completion?: Record<string, number>;
  completionByGender?: { G?: Record<string, number>; F?: Record<string, number>; T?: Record<string, number> };
}

export interface DataMetadata {
  genere_le: string;
  lecture_du_score: string;
  lecture_confiance?: string;
  normalisation?: string;
  ponderations?: Record<string, number>;
  justification_poids?: Record<string, string>;
  indicateurs?: Record<string, { label: string; sources?: string[]; note?: string }>;
  annee_choc?: string | number;
  limites?: string[];
  robustesse?: Record<string, { n_scenarios: number; spearman_moyen: number; spearman_min: number; top_k_identique: number }>;
}

export interface RegionalDataBundle {
  scores: RegionScore[];
  profiles: RegionProfile[];
  indicators: Record<string, Record<string, RegionIndicator>>;
  series: Record<string, { achevement?: { G?: Record<string, number>; F?: Record<string, number>; T?: Record<string, number> }; rang_par_annee?: Record<string, number> }>;
  metadata: DataMetadata;
}

@Injectable({ providedIn: 'root' })
export class RegionalDataService {
  private readonly http = inject(HttpClient);

  private readonly data$: Observable<RegionalDataBundle> = forkJoin({
    scores: this.http.get<RegionScore[]>('assets/data/indice.json'),
    profiles: this.http.get<RegionProfile[]>('assets/data/profils.json'),
    indicators: this.http.get<Record<string, Record<string, RegionIndicator>>>('assets/data/indicateurs.json'),
    series: this.http.get<RegionalDataBundle['series']>('assets/data/series.json'),
    metadata: this.http.get<DataMetadata>('assets/data/metadata.json'),
  }).pipe(shareReplay({ bufferSize: 1, refCount: false }));

  load(): Observable<RegionalDataBundle> {
    return this.data$;
  }

  toRegions(data: RegionalDataBundle): RegionData[] {
    const profileByCode = new Map(data.profiles.map((profile) => [profile.code, profile]));
    return data.scores.map((score) => ({
      ...score,
      profile: profileByCode.get(score.code),
      indicators: data.indicators[score.code],
      completion: data.series[score.code]?.achevement?.T,
      completionByGender: data.series[score.code]?.achevement,
    })).sort((a, b) => a.rang - b.rang);
  }

  referenceYear(data: RegionalDataBundle): string {
    const firstRegion = data.scores[0]?.code;
    return Object.keys(data.series[firstRegion ?? '']?.rang_par_annee ?? {}).sort().at(-1) ?? '2024/25';
  }
}
