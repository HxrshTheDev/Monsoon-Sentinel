import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EocDataService } from './services/eoc-data.service';
import { EocHeaderComponent } from './components/eoc-header.component';
import { EocNavRailComponent } from './components/eoc-nav-rail.component';
import { EocMapComponent } from './components/eoc-map.component';
import { EocTelemetryStripComponent } from './components/eoc-telemetry-strip.component';
import { EocIncidentsComponent } from './components/eoc-incidents.component';
import { EocDrainageComponent } from './components/eoc-drainage.component';
import { EocRoutesComponent } from './components/eoc-routes.component';
import { EocReportsComponent } from './components/eoc-reports.component';
import { EocHealthComponent } from './components/eoc-health.component';

@Component({
  selector: 'app-eoc',
  standalone: true,
  imports: [
    CommonModule,
    EocHeaderComponent,
    EocNavRailComponent,
    EocMapComponent,
    EocTelemetryStripComponent,
    EocIncidentsComponent,
    EocDrainageComponent,
    EocRoutesComponent,
    EocReportsComponent,
    EocHealthComponent,
  ],
  template: `
    <div class="eoc-shell">
      <app-eoc-header />
      <div class="eoc-body">
        <app-eoc-nav-rail />
        <main class="eoc-main">
          <div class="mode-banner" [class.live]="store.dataMode() === 'LIVE'">
            <strong>{{ store.dataMode() }}</strong>
            <span>{{ store.backendNote() }}</span>
          </div>
          <app-eoc-telemetry-strip />
          <div class="eoc-workspace">
            <section class="map-pane">
              <app-eoc-map />
            </section>
            <aside class="side-pane">
              @switch (store.activeView()) {
                @case ('drainage') { <app-eoc-drainage /> }
                @case ('routes') { <app-eoc-routes /> }
                @case ('alerts') { <app-eoc-incidents /> }
                @case ('timeline') { <app-eoc-incidents /> }
                @case ('reports') { <app-eoc-reports /> }
                @case ('health') { <app-eoc-health /> }
                @default { <app-eoc-incidents /> }
              }
            </aside>
          </div>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .eoc-shell {
      min-height: 100vh;
      background: #050b18;
      color: #e2e8f0;
      display: flex;
      flex-direction: column;
    }
    .eoc-body { display: flex; flex: 1; min-height: 0; }
    .eoc-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      padding: 0.75rem;
      gap: 0.65rem;
    }
    .mode-banner {
      display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;
      padding: 0.45rem 0.75rem; border-radius: 8px;
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid rgba(245, 158, 11, 0.35);
      font-size: 0.78rem;
    }
    .mode-banner.live {
      background: rgba(16, 185, 129, 0.12);
      border-color: rgba(16, 185, 129, 0.35);
    }
    .mode-banner strong { letter-spacing: 0.08em; font-size: 0.7rem; }
    .eoc-workspace {
      display: grid;
      grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
      gap: 0.75rem;
      flex: 1;
      min-height: 420px;
    }
    .map-pane, .side-pane {
      border: 1px solid rgba(56, 189, 248, 0.18);
      border-radius: 10px;
      overflow: hidden;
      background: #0a1224;
      min-height: 360px;
    }
    .side-pane { overflow: auto; }
    @media (max-width: 960px) {
      .eoc-workspace { grid-template-columns: 1fr; }
      .eoc-body { flex-direction: column; }
    }
  `]
})
export class EocComponent implements OnInit {
  readonly store = inject(EocDataService);

  ngOnInit(): void {
    this.store.loadFeeds();
    this.store.loadBackendSusceptibility();
  }
}
