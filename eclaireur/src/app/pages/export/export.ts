import { CommonModule } from '@angular/common';
import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RegionData, RegionalDataService } from '../../data/regional-data.service';

@Component({
  selector: 'app-export-page',
  imports: [CommonModule, FormsModule],
  templateUrl: './export.html',
  styleUrl: './export.css',
})
export class ExportPage implements OnInit {
  private readonly dataService = inject(RegionalDataService);
  readonly regions = signal<RegionData[]>([]);
  readonly selectedCode = signal('');
  readonly includeIndicators = signal(true);
  readonly includeContacts = signal(false);
  readonly year = signal('2024/25');
  readonly generatedAt = new Date();

  readonly selectedRegion = () => this.regions().find((region) => region.code === this.selectedCode());

  ngOnInit(): void {
    this.dataService.load().subscribe({
      next: (data) => {
        const regions = this.dataService.toRegions(data);
        this.regions.set(regions);
        this.selectedCode.set(regions[0]?.code ?? '');
        this.year.set(this.dataService.referenceYear(data));
      },
    });
  }

  downloadScores(): void {
    const rows = [['Code', 'Région', 'Score', 'Rang', 'Niveau', 'Confiance'], ...this.regions().map((r) => [r.code, r.region, String(r.score), String(r.rang), r.niveau, r.confiance])];
    this.download('eclaireur-classement.csv', rows.map((row) => row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(';')).join('\n'));
  }

  downloadJson(file: string): void {
    const link = document.createElement('a');
    link.href = `assets/data/${file}`;
    link.download = file;
    link.click();
  }

  printReport(): void { window.print(); }

  private download(name: string, content: string): void {
    const url = URL.createObjectURL(new Blob(['\ufeff', content], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
  }
}
