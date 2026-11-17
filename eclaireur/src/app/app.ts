import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { RegionalDataService } from './data/regional-data.service';

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  private readonly regionalData = inject(RegionalDataService);
  readonly referenceYear = signal('2024/25');

  ngOnInit(): void {
    this.regionalData.load().subscribe({
      next: (data) => this.referenceYear.set(this.regionalData.referenceYear(data)),
      error: () => undefined,
    });
  }
}
