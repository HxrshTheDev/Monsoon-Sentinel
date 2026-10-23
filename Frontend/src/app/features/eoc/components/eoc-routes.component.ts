import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EocDataService } from '../services/eoc-data.service';
import { VehicleKind } from '../models/eoc-models';
import { RoutePlanResult } from '../../../core/models/route.model';

@Component({
  selector: 'app-eoc-routes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="route-grid">
      <div class="panel">
        <div class="p-head"><div><h3>EMERGENCY ROUTE ADVISORY</h3><p>Road status · {{ store.horizon() }} · {{ store.dataMode() }}</p></div></div>
        @for (r of store.routes(); track r.id) {
          <div class="road" [class]="r.status.toLowerCase()">
            <div class="road-top"><strong>{{ r.roadName }}</strong><span class="rs">{{ r.status }}</span></div>
            <span class="corr">{{ r.corridor }}</span>
            <div class="road-meta">Flood depth <b>{{ r.floodDepthCm }} cm</b></div>
            <p>{{ r.recommendedAction }}</p>
            <button type="button" class="btn-loc" (click)="locate(r.path[0].lat, r.path[0].lng)">VIEW ON MAP</button>
          </div>
        }
      </div>

      <div class="panel">
        <h3>GENERATE SAFE ROUTE</h3>
        <p class="sub">Backend route over mapped Mumbai roads. Flood exposure is a model estimate, not live road status.</p>
        <label class="lbl" for="route-origin">ORIGIN</label>
        <input id="route-origin" name="route-origin" [(ngModel)]="sourceLocation" autocomplete="off" placeholder="e.g. Sion Circle">
        <label class="lbl" for="route-destination">DESTINATION</label>
        <input id="route-destination" name="route-destination" [(ngModel)]="destinationLocation" autocomplete="off" placeholder="e.g. BKC">
        <span class="lbl">VEHICLE</span>
        <div class="veh-grid">
          @for (v of vehicles; track v) {
            <button type="button" [class.on]="store.vehicle() === v" (click)="store.vehicle.set(v)">{{ v }}</button>
          }
        </div>
        <button type="button" class="btn-gen" [disabled]="store.safeRouteLoading()" (click)="store.generateSafeRoute(sourceLocation, destinationLocation)">
          {{ store.safeRouteLoading() ? 'REQUESTING ROUTE…' : 'GENERATE SAFE ROUTE' }}
        </button>
        @if (store.safeRouteError(); as error) {
          <p class="route-error" role="alert">{{ error }}</p>
        }
        @if (store.safeRoute(); as p) {
          @let route = p.recommendedRoute;
          <div class="plan">
            <span class="plan-veh">{{ store.vehicle() }} · BACKEND ROUTE · OPENSTREETMAP GEOMETRY</span>
            <strong>{{ p.source }} → {{ p.destination }}</strong>
            <div class="plan-grid">
              <div><em>Distance</em><b>{{ route.distanceKm }} km</b></div>
              <div><em>ETA</em><b>{{ route.etaMinutes }} min</b></div>
              <div><em>Modeled risk</em><b>{{ route.riskStatus }}</b></div>
            </div>
            <span class="plan-note">{{ route.riskExposureScore }} exposure · {{ route.unknownRiskEdgeCount ?? 0 }} edges without risk data</span>
            <span class="plan-note">{{ p.riskSource || 'Flood-risk source unavailable' }}. This is not confirmation that roads are currently safe or open.</span>
            @for (warning of p.warnings ?? []; track warning) {
              <span class="plan-note">{{ warning }}</span>
            }
            @if (p.alternativeRoute; as alternative) {
              <div class="alternative">
                <strong>Alternative: {{ alternative.name }}</strong>
                <span>{{ alternative.distanceKm }} km · {{ alternative.etaMinutes }} min · {{ alternative.riskStatus }} modeled risk</span>
              </div>
            } @else if (p.alternativeUnavailableReason) {
              <span class="plan-note">{{ p.alternativeUnavailableReason }}</span>
            }
            <button type="button" class="btn-loc" (click)="viewRoute(p)">VIEW ROUTE ON MAP</button>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .route-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 0.75rem; }
    .panel { background: rgba(15,23,42,0.75); border: 1px solid rgba(56,189,248,0.18); border-radius: 12px; padding: 1rem 1.1rem; display: flex; flex-direction: column; gap: 0.55rem; }
    h3 { margin: 0; font-size: 0.85rem; letter-spacing: 0.1em; color: #f1f5f9; }
    .p-head p, .sub { font-size: 0.66rem; color: #64748b; margin: 0.15rem 0 0; }
    .road { background: rgba(2,6,16,0.5); border: 1px solid rgba(148,163,184,0.14); border-left: 3px solid #38bdf8; border-radius: 8px; padding: 0.65rem 0.8rem; display: flex; flex-direction: column; gap: 0.2rem; }
    .road.closed { border-left-color: #ef4444; } .road.restricted { border-left-color: #fb923c; }
    .road.warning { border-left-color: #facc15; } .road.open { border-left-color: #34d399; }
    .road-top { display: flex; justify-content: space-between; align-items: center; }
    .road-top strong { font-size: 0.8rem; color: #fff; }
    .rs { font-size: 0.58rem; font-weight: 800; letter-spacing: 0.1em; color: #94a3b8; }
    .closed .rs { color: #f87171; } .restricted .rs { color: #fb923c; } .warning .rs { color: #facc15; } .open .rs { color: #34d399; }
    .corr { font-size: 0.64rem; color: #64748b; }
    .road-meta { font-size: 0.68rem; color: #94a3b8; } .road-meta b { color: #e2e8f0; }
    .road p { font-size: 0.7rem; color: #cbd5e1; margin: 0; }
    .btn-loc { align-self: flex-start; background: transparent; border: 1px solid #334155; color: #94a3b8; border-radius: 6px; padding: 0.35rem 0.7rem; font-size: 0.6rem; font-weight: 800; cursor: pointer; }
    .lbl { font-size: 0.58rem; font-weight: 800; letter-spacing: 0.14em; color: #64748b; }
    .veh-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.4rem; }
    .veh-grid button { background: rgba(2,6,16,0.5); border: 1px solid #334155; color: #94a3b8; border-radius: 7px; padding: 0.5rem 0; font-size: 0.64rem; font-weight: 800; cursor: pointer; }
    .veh-grid button.on { color: #22d3ee; border-color: #0ea5e9; background: rgba(14,165,233,0.12); }
    input { background: rgba(2,6,16,0.5); border: 1px solid #334155; border-radius: 7px; color: #e2e8f0; padding: 0.55rem; font-size: 0.7rem; }
    .btn-gen { background: linear-gradient(135deg, #0369a1, #0ea5e9); color: #fff; border: none; border-radius: 8px; padding: 0.7rem; font-size: 0.7rem; font-weight: 800; letter-spacing: 0.08em; cursor: pointer; }
    .btn-gen:disabled { opacity: 0.6; cursor: wait; }
    .route-error { color: #fca5a5; font-size: 0.7rem; margin: 0; }
    .plan { background: rgba(34,211,238,0.06); border: 1px solid rgba(34,211,238,0.35); border-radius: 8px; padding: 0.7rem 0.8rem; display: flex; flex-direction: column; gap: 0.3rem; }
    .plan-veh { font-size: 0.56rem; font-weight: 800; letter-spacing: 0.14em; color: #22d3ee; }
    .plan strong { font-size: 0.76rem; color: #fff; }
    .plan-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.4rem; }
    .plan-grid div { display: flex; flex-direction: column; }
    .plan-grid em { font-style: normal; font-size: 0.56rem; text-transform: uppercase; color: #64748b; }
    .plan-grid b { font-family: ui-monospace, monospace; font-size: 0.78rem; color: #f1f5f9; }
    .plan-note { font-size: 0.62rem; color: #64748b; }
    .alternative { display: flex; flex-direction: column; gap: 0.2rem; padding-top: 0.35rem; border-top: 1px solid rgba(148,163,184,0.14); color: #cbd5e1; font-size: 0.65rem; }
    .alternative span { color: #94a3b8; }
    @media (max-width: 1000px) { .route-grid { grid-template-columns: 1fr; } }
  `]
})
export class EocRoutesComponent {
  readonly store = inject(EocDataService);
  readonly vehicles: VehicleKind[] = ['CAR', 'SUV', 'TRUCK', 'RESCUE'];
  sourceLocation = 'Sion Circle';
  destinationLocation = 'Bandra-Kurla Complex (BKC)';

  locate(lat: number, lng: number): void {
    this.store.requestMapFocus(lat, lng, 13);
  }

  viewRoute(route: RoutePlanResult): void {
    this.store.activeView.set('overview');
    this.locate(route.sourceCoords[0], route.sourceCoords[1]);
  }
}
