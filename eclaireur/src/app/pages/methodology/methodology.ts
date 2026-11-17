import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DataMetadata, RegionalDataService } from '../../data/regional-data.service';

@Component({
  selector: 'app-methodology-page',
  imports: [CommonModule, RouterLink],
  templateUrl: './methodology.html',
  styleUrl: './methodology.css',
})
export class MethodologyPage implements OnInit {
  private readonly dataService = inject(RegionalDataService);
  readonly metadata = signal<DataMetadata | null>(null);
  readonly year = signal('2024/25');

  ngOnInit(): void {
    this.dataService.load().subscribe({
      next: (data) => {
        this.metadata.set(data.metadata);
        this.year.set(this.dataService.referenceYear(data));
      },
    });
  }

  percent(value: number): string {
    return `${(value * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`;
  }
}
