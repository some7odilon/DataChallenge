import { Routes } from '@angular/router';
import { DashboardPage } from './pages/dashboard/dashboard';
import { PriorityMapPage } from './pages/priority-map/priority-map';
import { RegionProfilePage } from './pages/region-profile/region-profile';
import { CompareRegionsPage } from './pages/compare-regions/compare-regions';
import { MethodologyPage } from './pages/methodology/methodology';
import { ExportPage } from './pages/export/export';

export const routes: Routes = [
  { path: 'dashboard', component: DashboardPage, title: 'Tableau de bord — Éclaireur' },
  { path: 'carte-des-priorites', component: PriorityMapPage, title: 'Carte des priorités — Éclaireur' },
  { path: 'fiche-regionale', component: RegionProfilePage, title: 'Fiche régionale — Éclaireur' },
  { path: 'comparer', component: CompareRegionsPage, title: 'Comparer les régions — Éclaireur' },
  { path: 'methode-et-limites', component: MethodologyPage, title: 'Méthode et limites — Éclaireur' },
  { path: 'export-et-impression', component: ExportPage, title: 'Export et impression — Éclaireur' },
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: '**', redirectTo: 'dashboard' },
];
