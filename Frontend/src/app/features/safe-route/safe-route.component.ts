import { Component, OnInit, AfterViewInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import * as L from 'leaflet';

import { RoutingService } from '../../core/services/routing.service';
import { RoutePlanResult, PresetRoute, RouteOption } from '../../core/models/route.model';

import { LoadingStateComponent } from '../../shared/components/loading-state/loading-state.component';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-safe-route',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    LoadingStateComponent,
    DecimalPipe
  ],
  template: `
    <div class="safe-route-page">
      <!-- Top Control & Route Planning Input Card -->
      <div class="card route-input-card">
        <div class="route-header-row">
          <div>
            <div class="title-with-badge">
              <h2 class="page-title">Safe Mobility & Route Planner</h2>
              <span class="badge-role">Flood-Avoidance Engine</span>
            </div>
            <p class="page-sub">Prototype arterial routing with flood-susceptibility penalties (curated BMC corridors — not a full city OSM network)</p>
          </div>
        </div>

        <div class="inputs-bar">
          <!-- From -->
          <div class="input-field-group">
            <span class="field-label">From (Origin):</span>
            <div class="input-wrap">
              <span class="dot-origin"></span>
              <input
                type="text"
                class="route-input"
                placeholder="Enter source location..."
                [(ngModel)]="sourceLocation"
              />
            </div>
          </div>

          <!-- Swap Button -->
          <button type="button" class="btn-swap" (click)="swapLocations()" title="Swap Origin and Destination">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="17 1 21 5 17 9"></polyline>
              <path d="M3 11V9a4 4 0 0 1 4-4h14"></path>
              <polyline points="7 23 3 19 7 15"></polyline>
              <path d="M21 13v2a4 4 0 0 1-4 4H3"></path>
            </svg>
          </button>

          <!-- To -->
          <div class="input-field-group">
            <span class="field-label">To (Destination):</span>
            <div class="input-wrap">
              <span class="dot-dest"></span>
              <input
                type="text"
                class="route-input"
                placeholder="Enter destination location..."
                [(ngModel)]="destinationLocation"
              />
            </div>
          </div>

          <!-- Vehicle Type -->
          <div class="input-field-group">
            <span class="field-label">Vehicle Type:</span>
            <div class="input-wrap">
              <select [(ngModel)]="vehicleType" class="route-input" style="padding-left: 0.75rem; cursor: pointer;">
                <option value="car">Car (Sedan/Hatch)</option>
                <option value="SUV">SUV (High Clearance)</option>
                <option value="truck">Heavy Commercial Truck</option>
                <option value="rescue">Emergency / Rescue Vehicle</option>
              </select>
            </div>
          </div>

          <button
            type="button"
            class="btn btn-primary btn-find"
            (click)="calculateRoute()"
            [disabled]="loading"
          >
            Find Safest Route
          </button>
        </div>

        <!-- Emergency Services Quick Target -->
        <div class="emergency-target-row">
          <span class="emergency-title">🚨 Emergency Facility Navigation:</span>
          <div class="emergency-chips">
            <button type="button" class="emergency-chip hospital" (click)="targetEmergencyFacility('hospital')">
              🏥 Nearest Hospital / Trauma Center
            </button>
            <button type="button" class="emergency-chip fire" (click)="targetEmergencyFacility('fire_station')">
              🚒 Nearest Fire & High-Water Rescue
            </button>
            <button type="button" class="emergency-chip police" (click)="targetEmergencyFacility('police')">
              🚓 Nearest Police Command Post
            </button>
          </div>
        </div>

        <!-- Presets -->
        <div class="presets-row">
          <span class="presets-title">Quick Scenarios:</span>
          <div class="preset-chips">
            @for (preset of presetRoutes; track preset.id) {
              <button
                type="button"
                class="preset-chip"
                [class.active]="sourceLocation === preset.source && destinationLocation === preset.destination"
                (click)="applyPreset(preset)"
              >
                {{ preset.label }}
              </button>
            }
          </div>
        </div>
      </div>

      <!-- Main Layout: Map & Comparison Cards -->
      <div class="route-main-grid">
        <!-- Leaflet Map -->
        <div class="card map-column">
          <div class="map-inner-wrap">
            <div #routeMapCanvas class="leaflet-map-canvas"></div>

            <!-- In-Map Semantic Legend -->
            <div class="route-map-legend">
              <div class="legend-row">
                <span class="legend-line route-safe-line"></span>
                <span>Safer route (flood-aware OSM path)</span>
              </div>
              @if (routePlan?.alternativeRoute) {
                <div class="legend-row">
                  <span class="legend-line route-alt-line"></span>
                  <span>Shortest road-network alternative</span>
                </div>
              }
              <div class="legend-row">
                <span class="hazard-dot"></span>
                <span>High-susceptibility edge</span>
              </div>
            </div>
          </div>
          @if (routeError) {
            <div class="map-error-banner">{{ routeError }}</div>
          }
        </div>

        <!-- Route Comparison Sidebar -->
        <div class="comparison-column">
          @if (loading) {
            <app-loading-state message="Snapping to OSM roads and calculating flood-aware paths..."></app-loading-state>
          } @else if (routeError && !routePlan) {
            <div class="card route-card" style="border-color: var(--status-unsafe);">
              <h4 class="route-name">No route displayed</h4>
              <p class="route-notes">{{ routeError }}</p>
              <p class="route-notes" style="margin-top: 0.5rem;">
                The map will not show a fake straight-line path when routing fails.
              </p>
            </div>
          } @else if (routePlan) {
            <!-- Card 1: Recommended Safe Route -->
            <button
              type="button"
              class="card route-card recommended-card selectable"
              [class.selected]="selectedRouteId === routePlan.recommendedRoute.id"
              (click)="selectRoute(routePlan.recommendedRoute.id)"
            >
              <div class="route-card-top">
                <div class="rec-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  SAFER ROUTE
                </div>
                <span class="safety-score font-mono status-safe">
                  {{ routePlan.recommendedRoute.safetyScore }}% SAFE
                </span>
              </div>

              <h4 class="route-name">{{ routePlan.recommendedRoute.name }}</h4>
              <p class="route-notes">{{ routePlan.recommendedRoute.notes }}</p>

              <div class="route-metrics-row">
                <div class="r-metric">
                  <span class="r-lbl">Distance</span>
                  <span class="r-val font-mono">{{ routePlan.recommendedRoute.distanceKm }} km</span>
                </div>
                <div class="r-metric">
                  <span class="r-lbl">Est. Time</span>
                  <span class="r-val font-mono">{{ routePlan.recommendedRoute.etaMinutes }} min</span>
                </div>
                <div class="r-metric">
                  <span class="r-lbl">Risk score</span>
                  <span class="r-val font-mono">{{ (routePlan.recommendedRoute.riskExposureScore ?? 0) | number:'1.2-2' }}</span>
                </div>
                <div class="r-metric">
                  <span class="r-lbl">High-risk edges</span>
                  <span class="r-val font-mono text-safe">{{ routePlan.recommendedRoute.highRiskEdgeCount ?? routePlan.recommendedRoute.floodPointsAvoided }}</span>
                </div>
              </div>
            </button>

            <!-- Card 2: Alternative (only when backend returns a distinct path) -->
            @if (routePlan.alternativeRoute; as alt) {
              <button
                type="button"
                class="card route-card alternative-card selectable"
                [class.selected]="selectedRouteId === alt.id"
                (click)="selectRoute(alt.id)"
              >
                <div class="route-card-top">
                  <span class="alt-badge">HIGHER-RISK ALTERNATIVE</span>
                  <span class="safety-score font-mono status-unsafe">
                    {{ alt.safetyScore }}% SAFE
                  </span>
                </div>

                <h4 class="route-name">{{ alt.name }}</h4>
                <p class="route-notes">{{ alt.notes }}</p>

                <div class="route-metrics-row">
                  <div class="r-metric">
                    <span class="r-lbl">Distance</span>
                    <span class="r-val font-mono">{{ alt.distanceKm }} km</span>
                  </div>
                  <div class="r-metric">
                    <span class="r-lbl">Est. Time</span>
                    <span class="r-val font-mono">{{ alt.etaMinutes }} min</span>
                  </div>
                  <div class="r-metric">
                    <span class="r-lbl">Risk score</span>
                    <span class="r-val font-mono">{{ (alt.riskExposureScore ?? 0) | number:'1.2-2' }}</span>
                  </div>
                  <div class="r-metric">
                    <span class="r-lbl">Exposure</span>
                    <span class="badge status-unsafe">{{ alt.hazardExposure }}</span>
                  </div>
                </div>

                <div class="alternative-disclaimer">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  <span>
                    Trade-off uses backend distance, time, and length-weighted susceptibility — not frontend estimates.
                  </span>
                </div>
              </button>
            } @else {
              <div class="card route-card alt-unavailable">
                <span class="alt-badge">NO DISTINCT ALTERNATIVE</span>
                <p class="route-notes">
                  {{ routePlan.alternativeUnavailableReason || 'Only one feasible arterial corridor was found between these endpoints.' }}
                </p>
              </div>
            }

            @if (routePlan.networkProvenance) {
              <p class="provenance-note">{{ routePlan.networkProvenance }}</p>
            }

            <!-- Active Hazards on Route -->
            <div class="card hazards-card">
              <div class="card-header" style="margin-bottom: 0.5rem;">
                <span class="card-title" style="font-size: 0.95rem;">Active Road Hazards ({{ routePlan.hazards.length }})</span>
              </div>
              <div class="hazards-list">
                @for (haz of routePlan.hazards; track haz.id) {
                  <div class="hazard-item">
                    <div class="h-top">
                      <span class="h-name font-mono">{{ haz.title }}</span>
                      <span class="badge" [ngClass]="haz.severity === 'UNSAFE' ? 'status-critical' : 'status-caution'">
                        {{ haz.waterDepthCm }} cm depth
                      </span>
                    </div>
                    <span class="h-location">{{ haz.location }}</span>
                    <span class="h-status">{{ haz.status }}</span>
                  </div>
                }
              </div>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .safe-route-page {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .title-with-badge {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .page-title {
      font-size: 1.45rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .page-sub {
      font-size: 0.825rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    .route-input-card {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .inputs-bar {
      display: flex;
      align-items: flex-end;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .input-field-group {
      flex: 1;
      min-width: 220px;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .field-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .input-wrap {
      position: relative;
      display: flex;
      align-items: center;
    }
    .dot-origin {
      position: absolute;
      left: 0.85rem;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: var(--status-safe);
      box-shadow: 0 0 8px var(--status-safe);
    }
    .dot-dest {
      position: absolute;
      left: 0.85rem;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: var(--brand-primary);
      box-shadow: 0 0 8px var(--brand-primary);
    }
    .route-input {
      width: 100%;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.55rem 1rem 0.55rem 2.2rem;
      color: var(--text-main);
      font-size: 0.875rem;
      outline: none;
      transition: border-color var(--transition-fast);

      &:focus {
        border-color: var(--brand-primary);
      }
    }

    .btn-swap {
      height: 40px;
      width: 40px;
      border-radius: var(--radius-md);
      background-color: var(--bg-card-hover);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      &:hover {
        color: var(--text-main);
        border-color: var(--text-dim);
      }
    }
    .btn-find {
      height: 40px;
      padding: 0 1.25rem;
    }

    // Presets Row
    .presets-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border-light);
    }
    .presets-title {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .preset-chips {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .preset-chip {
      font-size: 0.75rem;
      padding: 0.25rem 0.65rem;
      border-radius: var(--radius-full);
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      transition: all var(--transition-fast);

      &:hover {
        color: var(--text-main);
      }
      &.active {
        background-color: rgba(59, 130, 246, 0.15);
        border-color: var(--brand-primary);
        color: #ffffff;
      }
    }

    /* Emergency Target Row */
    .emergency-target-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border-subtle);
      flex-wrap: wrap;
    }
    .emergency-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: #f87171;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .emergency-chips {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .emergency-chip {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.35rem 0.75rem;
      border-radius: var(--radius-full);
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      transition: all var(--transition-fast);
    }
    .emergency-chip.hospital {
      border-color: rgba(239, 68, 68, 0.4);
      background: rgba(239, 68, 68, 0.08);
      color: #fca5a5;
    }
    .emergency-chip.hospital:hover {
      background: rgba(239, 68, 68, 0.2);
      border-color: #ef4444;
      color: #ffffff;
    }
    .emergency-chip.fire {
      border-color: rgba(249, 115, 22, 0.4);
      background: rgba(249, 115, 22, 0.08);
      color: #fdba74;
    }
    .emergency-chip.fire:hover {
      background: rgba(249, 115, 22, 0.2);
      border-color: #f97316;
      color: #ffffff;
    }
    .emergency-chip.police {
      border-color: rgba(59, 130, 246, 0.4);
      background: rgba(59, 130, 246, 0.08);
      color: #93c5fd;
    }
    .emergency-chip.police:hover {
      background: rgba(59, 130, 246, 0.2);
      border-color: #3b82f6;
      color: #ffffff;
    }

    // Main Grid
    .route-main-grid {
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 1.25rem;
      @media (max-width: 1100px) {
        grid-template-columns: 1fr;
      }
    }

    .map-column {
      padding: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .map-inner-wrap {
      position: relative;
      width: 100%;
      height: clamp(320px, 55vh, 640px);
      min-height: 320px;
    }
    .leaflet-map-canvas {
      width: 100%;
      height: 100%;
      min-height: 320px;
      z-index: 1;
    }
    .map-error-banner {
      padding: 0.65rem 1rem;
      background: rgba(239, 68, 68, 0.12);
      color: #fecaca;
      font-size: 0.8125rem;
      border-top: 1px solid rgba(239, 68, 68, 0.35);
    }
    .selectable {
      cursor: pointer;
      text-align: left;
      width: 100%;
      font: inherit;
      color: inherit;
    }
    .selectable.selected {
      outline: 2px solid #10b981;
      outline-offset: 1px;
    }
    .alternative-card.selectable.selected {
      outline-color: #f97316;
    }
    .alt-unavailable {
      border-color: rgba(148, 163, 184, 0.35);
      opacity: 0.95;
    }
    .provenance-note {
      font-size: 0.72rem;
      color: var(--text-dim);
      line-height: 1.4;
      margin: 0;
      padding: 0 0.25rem;
    }
    @media (max-width: 700px) {
      .map-inner-wrap {
        height: min(70vh, 520px);
        min-height: 280px;
      }
      .route-metrics-row {
        grid-template-columns: repeat(2, 1fr) !important;
      }
    }
    .route-map-legend {
      position: absolute;
      bottom: 20px;
      left: 20px;
      background: rgba(15, 23, 42, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 0.65rem 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      z-index: 500;
      font-size: 0.75rem;
    }
    .legend-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      color: var(--text-main);
    }
    .legend-line {
      width: 24px;
      height: 4px;
      border-radius: 2px;
    }
    .route-safe-line {
      background-color: #10b981;
    }
    .route-alt-line {
      background: repeating-linear-gradient(90deg, #f97316, #f97316 4px, transparent 4px, transparent 8px);
    }
    .hazard-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: #ef4444;
      box-shadow: 0 0 6px #ef4444;
    }

    // Comparison Column
    .comparison-column {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .route-card {
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
    }
    .recommended-card {
      border-color: rgba(16, 185, 129, 0.4);
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.05) 0%, var(--bg-card) 100%);
    }
    .alternative-card {
      border-color: rgba(249, 115, 22, 0.35);
    }
    .route-card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .rec-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.72rem;
      font-weight: 700;
      color: #10b981;
      letter-spacing: 0.04em;
    }
    .alt-badge {
      font-size: 0.72rem;
      font-weight: 700;
      color: #f97316;
      letter-spacing: 0.04em;
    }
    .safety-score {
      font-size: 0.875rem;
      font-weight: 700;
      padding: 0.15rem 0.5rem;
      border-radius: var(--radius-sm);
    }
    .route-name {
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--text-main);
      margin: 0;
    }
    .route-notes {
      font-size: 0.8125rem;
      color: var(--text-muted);
      line-height: 1.4;
      margin: 0;
    }

    .route-metrics-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.5rem 0.65rem;
      gap: 0.5rem;
      margin-top: 0.35rem;
    }
    .r-metric {
      display: flex;
      flex-direction: column;
    }
    .r-lbl {
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .r-val {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .text-safe {
      color: var(--status-safe);
    }

    .alternative-disclaimer {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: #fed7aa;
      background-color: rgba(249, 115, 22, 0.1);
      border-left: 3px solid #f97316;
      padding: 0.4rem 0.6rem;
      border-radius: 2px;
      line-height: 1.35;
    }

    // Hazards Card
    .hazards-card {
      padding: 0.85rem 1rem;
    }
    .hazards-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .hazard-item {
      display: flex;
      flex-direction: column;
      background-color: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.5rem 0.65rem;
      gap: 0.15rem;
    }
    .h-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .h-name {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .h-location {
      font-size: 0.72rem;
      color: var(--text-muted);
    }
    .h-status {
      font-size: 0.7rem;
      color: var(--status-unsafe);
    }
  `]
})
export class SafeRouteComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('routeMapCanvas') routeMapCanvas!: ElementRef;

  sourceLocation = 'CSMT Fort';
  destinationLocation = 'CSMIA International Airport';
  vehicleType = 'car';
  presetRoutes: PresetRoute[] = [];
  routePlan: RoutePlanResult | null = null;
  selectedRouteId: string | null = null;
  routeError: string | null = null;
  loading = false;
  emergencyFacilities: any[] = [
    { id: 'FAC-HOSP-01', name: 'King Edward Memorial Hospital (KEM Hospital)', type: 'hospital', category: 'Level 1 Trauma Center', lat: 19.0028, lon: 72.8431, phone: '022-24107000' },
    { id: 'FAC-HOSP-02', name: 'Lokmanya Tilak Municipal General Hospital (Sion Hospital)', type: 'hospital', category: 'Metropolitan Disaster Trauma Center', lat: 19.0378, lon: 72.8606, phone: '022-24076381' },
    { id: 'FAC-HOSP-03', name: 'Lilavati Hospital & Research Centre', type: 'hospital', category: 'Emergency Cardiac & Trauma', lat: 19.0514, lon: 72.8295, phone: '022-26751000' },
    { id: 'FAC-HOSP-04', name: 'Kokilaben Dhirubhai Ambani Hospital', type: 'hospital', category: 'Western Suburbs Trauma Center', lat: 19.1312, lon: 72.8252, phone: '022-42696969' },
    { id: 'FAC-HOSP-05', name: 'K. B. Bhabha Municipal General Hospital Kurla', type: 'hospital', category: 'Suburban Municipal Trauma Center', lat: 19.0650, lon: 72.8790, phone: '022-26500241' },
    { id: 'FAC-FIRE-01', name: 'Mumbai Fire Brigade Headquarters (Byculla)', type: 'fire_station', category: 'Metropolitan Dispatch', lat: 18.9780, lon: 72.8310, phone: '101' },
    { id: 'FAC-FIRE-02', name: 'Andheri Fire & Rescue Station', type: 'fire_station', category: 'Mid-Suburbs Heavy Rescue Hub', lat: 19.1180, lon: 72.8490, phone: '101' },
    { id: 'FAC-FIRE-03', name: 'Kurla Fire & Rescue Station', type: 'fire_station', category: 'Mithi Catchment Flood Dispatch', lat: 19.0680, lon: 72.8780, phone: '101' },
    { id: 'FAC-FIRE-04', name: 'Bandra Fire Station', type: 'fire_station', category: 'Coastal Rescue Unit', lat: 19.0550, lon: 72.8350, phone: '101' },
    { id: 'FAC-POL-01', name: 'Mumbai Police Commissionerate Headquarters', type: 'police', category: 'Metropolitan Command & Control', lat: 18.9440, lon: 72.8340, phone: '100 / 112' },
    { id: 'FAC-POL-02', name: 'Bandra Police Divisional Headquarters', type: 'police', category: 'Western Suburbs Traffic & Safety Command', lat: 19.0550, lon: 72.8350, phone: '100 / 112' },
    { id: 'FAC-POL-03', name: 'Kurla Police Station Hub', type: 'police', category: 'Central Suburbs Disaster Division', lat: 19.0670, lon: 72.8795, phone: '100 / 112' },
    { id: 'FAC-POL-04', name: 'Andheri Police Station', type: 'police', category: 'Suburban Arterial Safety Division', lat: 19.1190, lon: 72.8470, phone: '100 / 112' }
  ];

  private map?: L.Map;
  private routeLayersGroup = L.layerGroup();
  private emergencyLayersGroup = L.layerGroup();
  private resizeObserver?: ResizeObserver;
  private resizeHandler = () => this.map?.invalidateSize();

  constructor(
    private routingService: RoutingService,
    private route: ActivatedRoute,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.loadPresets();
    this.loadEmergencyFacilities();
    this.route.queryParams.subscribe(params => {
      if (params['from']) this.sourceLocation = params['from'];
      if (params['to']) this.destinationLocation = params['to'];
      if (params['vehicle']) this.vehicleType = params['vehicle'];
    });
  }

  private loadEmergencyFacilities(): void {
    this.http.get<any[]>(`${environment.apiBaseUrl}/api/v1/emergency/facilities`).subscribe({
      next: (facs) => {
        if (facs && facs.length > 0) {
          this.emergencyFacilities = facs;
        }
        this.renderEmergencyMarkers();
      },
      error: () => {
        // Fallback pre-populated
        this.renderEmergencyMarkers();
      }
    });
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.initRouteMap();
      this.calculateRoute();
    }, 120);
  }

  ngOnDestroy(): void {
    window.removeEventListener('resize', this.resizeHandler);
    this.resizeObserver?.disconnect();
    if (this.map) {
      this.map.remove();
      this.map = undefined;
    }
  }

  private loadPresets(): void {
    this.routingService.getPresetRoutes().subscribe(presets => {
      this.presetRoutes = presets;
    });
  }

  private initRouteMap(): void {
    if (!this.routeMapCanvas?.nativeElement) return;
    if (this.map) {
      this.map.remove();
      this.map = undefined;
    }

    const el = this.routeMapCanvas.nativeElement as HTMLElement;
    this.map = L.map(el, {
      center: [environment.defaultMapCenter.lat, environment.defaultMapCenter.lon],
      zoom: 12,
      zoomControl: false,
      attributionControl: false
    });

    L.control.zoom({ position: 'topright' }).addTo(this.map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      subdomains: ['a', 'b', 'c']
    }).addTo(this.map);

    this.emergencyLayersGroup.addTo(this.map);
    this.routeLayersGroup.addTo(this.map);
    this.renderEmergencyMarkers();

    window.addEventListener('resize', this.resizeHandler);
    if (typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => {
        this.map?.invalidateSize({ animate: false });
      });
      this.resizeObserver.observe(el);
    }

    setTimeout(() => this.map?.invalidateSize(), 50);
    setTimeout(() => this.map?.invalidateSize(), 300);
  }

  selectRoute(routeId: string): void {
    this.selectedRouteId = routeId;
    if (this.routePlan) {
      this.renderRouteOnMap(this.routePlan);
    }
  }

  targetEmergencyFacility(type: string): void {
    const matching = this.emergencyFacilities.filter(f => f.type === type);
    if (matching.length > 0) {
      // Pick first matching or nearest
      const target = matching[0];
      this.destinationLocation = target.name;
      this.calculateRoute();
    }
  }

  private renderEmergencyMarkers(): void {
    if (!this.map) return;
    this.emergencyLayersGroup.clearLayers();

    this.emergencyFacilities.forEach(fac => {
      let iconSymbol = '🏥';
      let bgColor = '#ef4444';
      if (fac.type === 'fire_station') {
        iconSymbol = '🚒';
        bgColor = '#f97316';
      } else if (fac.type === 'police') {
        iconSymbol = '🚓';
        bgColor = '#3b82f6';
      }

      const customIcon = L.divIcon({
        className: 'emergency-poi-marker',
        html: `
          <div style="background-color: ${bgColor}; border: 2px solid #ffffff; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 0 10px ${bgColor}; cursor: pointer;">
            ${iconSymbol}
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const marker = L.marker([fac.lat, fac.lon], { icon: customIcon });
      marker.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px;">
          <strong>${fac.name}</strong><br/>
          <span style="color: #64748b;">${fac.category || fac.type}</span><br/>
          ${fac.phone ? '📞 ' + fac.phone + '<br/>' : ''}
          <span style="color: #10b981; font-weight: bold;">⚡ Click to navigate here</span>
        </div>
      `);

      marker.on('click', () => {
        this.destinationLocation = fac.name;
        this.calculateRoute();
      });

      this.emergencyLayersGroup.addLayer(marker);
    });
  }

  calculateRoute(): void {
    this.loading = true;
    this.routeError = null;
    this.routingService.calculateSafeRoute(this.sourceLocation, this.destinationLocation, this.vehicleType).subscribe({
      next: plan => {
        const coords = plan?.recommendedRoute?.pathCoordinates;
        if (!coords || coords.length < 2) {
          this.loading = false;
          this.routePlan = null;
          this.routeLayersGroup.clearLayers();
          this.routeError = 'Backend returned an empty route geometry. No path was drawn.';
          return;
        }
        this.routePlan = plan;
        this.selectedRouteId = plan.recommendedRoute.id;
        this.renderRouteOnMap(plan);
        this.loading = false;
        setTimeout(() => this.map?.invalidateSize(), 80);
      },
      error: (err) => {
        this.loading = false;
        this.routePlan = null;
        this.routeLayersGroup.clearLayers();
        const detail = err?.error?.detail;
        this.routeError = typeof detail === 'string'
          ? detail
          : 'Route calculation failed. Confirm the backend is reachable and both points snap to the Mumbai road network.';
      }
    });
  }

  swapLocations(): void {
    const temp = this.sourceLocation;
    this.sourceLocation = this.destinationLocation;
    this.destinationLocation = temp;
    this.calculateRoute();
  }

  applyPreset(preset: PresetRoute): void {
    this.sourceLocation = preset.source;
    this.destinationLocation = preset.destination;
    this.calculateRoute();
  }

  private renderRouteOnMap(plan: RoutePlanResult): void {
    if (!this.map) return;
    this.routeLayersGroup.clearLayers();
    this.map.invalidateSize({ animate: false });

    // Leaflet expects [lat, lon] — backend pathCoordinates use that order.
    const toLatLngs = (pts: [number, number][]): L.LatLngExpression[] =>
      pts
        .filter((p) => Array.isArray(p) && p.length >= 2 && Number.isFinite(p[0]) && Number.isFinite(p[1]))
        .map((p) => [p[0], p[1]] as L.LatLngExpression);

    const safeLatLngs = toLatLngs(plan.recommendedRoute.pathCoordinates as [number, number][]);
    if (safeLatLngs.length < 2) {
      this.routeError = 'Route geometry is invalid; nothing drawn on the map.';
      return;
    }

    const selectedId = this.selectedRouteId || plan.recommendedRoute.id;
    const safeSelected = selectedId === plan.recommendedRoute.id;
    const alt = plan.alternativeRoute;
    const altSelected = !!alt && selectedId === alt.id;

    // Draw alternative first (under), then safer on top — selected gets casing + heavier stroke
    let altPolyline: L.Polyline | null = null;
    const altLatLngs = alt?.pathCoordinates?.length
      ? toLatLngs(alt.pathCoordinates as [number, number][])
      : [];
    if (altLatLngs.length >= 2) {
      if (altSelected) {
        this.routeLayersGroup.addLayer(L.polyline(altLatLngs, {
          color: '#7c2d12',
          weight: 10,
          opacity: 0.55,
          interactive: false,
          smoothFactor: 0
        }));
      }
      altPolyline = L.polyline(altLatLngs, {
        color: '#f97316',
        weight: altSelected ? 7 : 4,
        dashArray: altSelected ? undefined : '10, 8',
        opacity: altSelected ? 0.95 : 0.65,
        smoothFactor: 0
      });
      altPolyline.bindTooltip(
        `<strong>${alt!.name}</strong><br/>${alt!.distanceKm} km • ${alt!.etaMinutes} min • risk ${alt!.riskExposureScore ?? '—'}`
      );
      altPolyline.on('click', () => this.selectRoute(alt!.id));
      this.routeLayersGroup.addLayer(altPolyline);
    }

    if (safeSelected) {
      this.routeLayersGroup.addLayer(L.polyline(safeLatLngs, {
        color: '#064e3b',
        weight: 10,
        opacity: 0.5,
        interactive: false,
        smoothFactor: 0
      }));
    }
    const safePolyline = L.polyline(safeLatLngs, {
      color: '#10b981',
      weight: safeSelected ? 7 : 4,
      opacity: safeSelected ? 0.95 : 0.55,
      smoothFactor: 0
    });
    safePolyline.bindTooltip(
      `<strong>${plan.recommendedRoute.name}</strong><br/>` +
      `${plan.recommendedRoute.distanceKm} km • ${plan.recommendedRoute.etaMinutes} min • risk ${plan.recommendedRoute.riskExposureScore ?? '—'}`
    );
    safePolyline.on('click', () => this.selectRoute(plan.recommendedRoute.id));
    this.routeLayersGroup.addLayer(safePolyline);

    const originIcon = L.divIcon({
      className: 'custom-map-pin',
      html: `<div style="background-color: #10b981; border: 2px solid #ffffff; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px;">A</div>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
    const originMarker = L.marker(plan.sourceCoords as L.LatLngExpression, { icon: originIcon });
    originMarker.bindTooltip(`<strong>Origin:</strong> ${plan.source}`);
    this.routeLayersGroup.addLayer(originMarker);

    const destIcon = L.divIcon({
      className: 'custom-map-pin',
      html: `<div style="background-color: #3b82f6; border: 2px solid #ffffff; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px;">B</div>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
    const destMarker = L.marker(plan.destCoords as L.LatLngExpression, { icon: destIcon });
    destMarker.bindTooltip(`<strong>Destination:</strong> ${plan.destination}`);
    this.routeLayersGroup.addLayer(destMarker);

    (plan.hazards || []).forEach(h => {
      const hazardIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `<div style="background-color: #ef4444; border: 2px solid #ffffff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; box-shadow: 0 0 10px #ef4444;">⚠</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      const marker = L.marker(h.coordinates as L.LatLngExpression, { icon: hazardIcon });
      marker.bindTooltip(
        `<strong>${h.title}</strong><br/>Status: ${h.status}<br/><em>Proxy susceptibility (depth unmeasured)</em>`
      );
      this.routeLayersGroup.addLayer(marker);
    });

    const bounds = L.latLngBounds(safeLatLngs);
    bounds.extend(plan.sourceCoords as L.LatLngExpression);
    bounds.extend(plan.destCoords as L.LatLngExpression);
    if (altPolyline) {
      bounds.extend(altPolyline.getBounds());
    }
    this.map.fitBounds(bounds.pad(0.12), { padding: [36, 36], maxZoom: 15 });
  }
}
