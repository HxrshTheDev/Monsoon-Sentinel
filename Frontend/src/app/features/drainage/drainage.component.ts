import { Component, OnInit, AfterViewInit, ElementRef, ViewChild, OnDestroy, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';
import { environment } from '../../../environments/environment';

export interface DrainageNode3D {
  id: string;
  name: string;
  type: string;
  basin: string;
  lat: number;
  lon: number;
  surface_elevation_m: number;
  invert_elevation_m: number;
  depth_m: number;
  description: string;
  screenX?: number;
  screenY?: number;
}

export interface DrainageEdge3D {
  id: string;
  name: string;
  type: string;
  source_node: string;
  target_node: string;
  length_m: number;
  width_m: number;
  height_m: number;
  shape: string;
  manning_n: number;
  slope: number;
  manning_capacity_m3s: number;
  catchment_area_ha: number;
  runoff_coeff: number;
}

export interface HydraulicInspection {
  pipe_id: string;
  pipe_name: string;
  pipe_type: string;
  source_node: DrainageNode3D;
  target_node: DrainageNode3D;
  hydraulic_status: 'UNDERFLOW' | 'TRANSITION' | 'OVERFLOW_SURCHARGE';
  severity_level: 'SAFE' | 'ALERT' | 'CRITICAL';
  parameters: {
    rainfall_intensity_mm_h: number;
    catchment_area_ha: number;
    runoff_coefficient: number;
    conduit_length_m: number;
    bed_slope_pct: number;
    manning_roughness_n: number;
    cross_sectional_area_m2: number;
    hydraulic_radius_m: number;
    full_capacity_m3s: number;
    inflow_discharge_m3s: number;
    capacity_utilization_pct: number;
    water_velocity_m_s: number;
    estimated_flow_depth_m: number;
    surcharge_rate_m3s: number;
    surcharge_head_m: number;
    freeboard_m: number;
  };
  engineering_verdict: string;
  timestamp: string;
}

@Component({
  selector: 'app-drainage-3d',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="drainage-page">
      <!-- Top Title & Controls Header -->
      <div class="drainage-header">
        <div>
          <div class="header-badge-row">
            <h1 class="page-title">Greater Mumbai Drainage Network & Hydraulic Modeling (BRIMSTOWAD)</h1>
            <span class="badge-status-3d">PHYSICAL HYDRAULICS</span>
            <span class="badge-crs">UTM 43N (MSL Datum)</span>
          </div>
          <p class="page-subtitle">
            Authentic node-and-conduit mapping with real DEM elevations, Manning conveyance capacity, and Rational method surcharge prediction.
          </p>
        </div>

        <div class="header-actions">
          <!-- View Mode Switcher -->
          <div class="view-mode-tabs">
            <button
              type="button"
              class="tab-btn"
              [class.active]="viewMode === 'GIS_MAP'"
              (click)="switchViewMode('GIS_MAP')"
            >
              🗺️ GIS Drainage Map
            </button>
            <button
              type="button"
              class="tab-btn"
              [class.active]="viewMode === '3D_ISOMETRIC'"
              (click)="switchViewMode('3D_ISOMETRIC')"
            >
              🌐 3D Elevation Mesh
            </button>
          </div>

          <!-- 3D Camera Controls -->
          @if (viewMode === '3D_ISOMETRIC') {
            <div class="view-controls">
              <button class="btn-ctrl" (click)="resetCamera()" title="Reset Camera View">
                Isometric
              </button>
              <button class="btn-ctrl" (click)="setTopView()" title="Top-down Ortho View">
                Top-Down
              </button>
              <button class="btn-ctrl" (click)="toggleElevationExaggeration()">
                Z-Scale: {{ zScale }}x
              </button>
            </div>
          }
        </div>
      </div>

      <!-- Main Layout: Viewport + Engineering Inspector -->
      <div class="drainage-layout">
        <!-- Map / 3D Canvas Viewport -->
        <div class="viewport-card">
          <!-- Mode A: GIS Map View (Leaflet) -->
          <div
            class="leaflet-container-wrap"
            [style.display]="viewMode === 'GIS_MAP' ? 'block' : 'none'"
          >
            <div #gisMapRef class="drainage-leaflet-canvas"></div>
          </div>

          <!-- Mode B: 3D Isometric View (Canvas) -->
          <div
            class="canvas-container"
            #containerRef
            [style.display]="viewMode === '3D_ISOMETRIC' ? 'block' : 'none'"
          >
            <canvas #canvasRef
              (mousedown)="onMouseDown($event)"
              (mousemove)="onMouseMove($event)"
              (mouseup)="onMouseUp()"
              (wheel)="onWheel($event)"
              (click)="onCanvasClick($event)">
            </canvas>
          </div>

          <!-- HUD Overlay (Shared across both modes) -->
          <div class="canvas-hud">
            <div class="hud-item">
              <span class="hud-label">Nodes (Manholes/Outfalls)</span>
              <span class="hud-val font-mono">{{ nodes.length }}</span>
            </div>
            <div class="hud-divider"></div>
            <div class="hud-item">
              <span class="hud-label">Conduits / Canals</span>
              <span class="hud-val font-mono">{{ edges.length }}</span>
            </div>
            <div class="hud-divider"></div>
            <div class="hud-item">
              <span class="hud-label">Elevation Range</span>
              <span class="hud-val font-mono">{{ bounds.minElev }}m – {{ bounds.maxElev }}m MSL</span>
            </div>
            <div class="hud-divider"></div>
            <div class="hud-item">
              <span class="hud-label">Active Conduit</span>
              <span class="hud-val font-mono highlight-name">{{ selectedEdge ? selectedEdge.name : 'Click conduit' }}</span>
            </div>
          </div>

          <!-- Legend Overlay -->
          <div class="canvas-legend">
            <span class="leg-title">Hydraulic Conveyance State</span>
            <div class="leg-item">
              <span class="leg-dot underflow"></span>
              <span>Underflow (Q &lt; 75% Cap) — Safe</span>
            </div>
            <div class="leg-item">
              <span class="leg-dot transition"></span>
              <span>Transition (75–100% Cap) — Alert</span>
            </div>
            <div class="leg-item">
              <span class="leg-dot overflow"></span>
              <span>Surcharge Overflow (&gt; 100%) — Critical</span>
            </div>
            <div class="leg-item">
              <span class="leg-dot node-dot"></span>
              <span>Manhole / Intake / Outfall Node</span>
            </div>
          </div>

          <!-- Quick Interactive Hint -->
          <div class="viewport-footer-hint">
            <span>💡 Click any conduit on the map or 3D view to inspect Manning capacity and predict overflow under storm intensity.</span>
          </div>
        </div>

        <!-- Right: Engineering Hydraulic Inspector -->
        <div class="inspector-card">
          <div class="inspector-header">
            <div>
              <span class="inspector-label">Engineering Diagnostic</span>
              <h2 class="inspector-title">Hydraulic Solver & Inspector</h2>
            </div>
            <span class="pill-solver font-mono">Manning 1D / Rational</span>
          </div>

          @if (inspection && selectedEdge) {
            <div class="inspector-body">
              <!-- Selected Conduit Identifier -->
              <div class="conduit-badge-card">
                <div class="conduit-top">
                  <span class="c-type font-mono">{{ selectedEdge.type }}</span>
                  <span class="c-id font-mono">{{ selectedEdge.id }}</span>
                </div>
                <h3 class="c-name">{{ selectedEdge.name }}</h3>
                <p class="c-sub">Connecting <strong>{{ inspection.source_node.name }}</strong> → <strong>{{ inspection.target_node.name }}</strong></p>
              </div>

              <!-- Rainfall Intensity Control -->
              <div class="param-control-card">
                <div class="param-header">
                  <span class="p-title">Storm Rainfall Intensity (I)</span>
                  <span class="p-value font-mono">{{ rainfallIntensity }} mm/h</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="120"
                  step="5"
                  [(ngModel)]="rainfallIntensity"
                  (input)="onRainfallChange()"
                  class="rainfall-slider"
                />
                <div class="slider-presets">
                  <button (click)="setPresetRainfall(20)">Shower (20)</button>
                  <button (click)="setPresetRainfall(45)">Monsoon (45)</button>
                  <button (click)="setPresetRainfall(70)">Heavy (70)</button>
                  <button (click)="setPresetRainfall(110)">2015 Cloudburst (110)</button>
                </div>
              </div>

              <!-- Verdict Alert Banner -->
              <div class="verdict-card" [ngClass]="inspection.severity_level.toLowerCase()">
                <div class="verdict-icon">
                  @if (inspection.hydraulic_status === 'UNDERFLOW') { 🟢 }
                  @else if (inspection.hydraulic_status === 'TRANSITION') { 🟡 }
                  @else { 🔴 }
                </div>
                <div class="verdict-content">
                  <span class="verdict-title">{{ inspection.hydraulic_status }} ({{ inspection.severity_level }})</span>
                  <p class="verdict-desc">{{ inspection.engineering_verdict }}</p>
                </div>
              </div>

              <!-- Real-world Engineering Metrics Grid -->
              <div class="metrics-grid">
                <!-- Metric 1: Capacity Utilization -->
                <div class="metric-card">
                  <span class="m-label">Capacity Load</span>
                  <div class="m-val font-mono">
                    {{ inspection.parameters.capacity_utilization_pct }}%
                  </div>
                  <div class="util-bar">
                    <div
                      class="util-fill"
                      [style.width.%]="mathMin(inspection.parameters.capacity_utilization_pct, 100)"
                      [ngClass]="inspection.severity_level.toLowerCase()"
                    ></div>
                  </div>
                  <span class="m-sub font-mono">Full-barrel threshold</span>
                </div>

                <!-- Metric 2: Surcharge Flow Rate -->
                <div class="metric-card">
                  <span class="m-label">Surface Overflow</span>
                  <div class="m-val font-mono" [class.text-danger]="inspection.parameters.surcharge_rate_m3s > 0">
                    {{ inspection.parameters.surcharge_rate_m3s }} <small>m³/s</small>
                  </div>
                  <span class="m-sub font-mono">
                    {{ inspection.parameters.surcharge_rate_m3s > 0 ? 'Exiting manhole rims' : 'Zero surface breach' }}
                  </span>
                </div>

                <!-- Metric 3: Rational Runoff Inflow -->
                <div class="metric-card">
                  <span class="m-label">Runoff Inflow (Qin)</span>
                  <div class="m-val font-mono">
                    {{ inspection.parameters.inflow_discharge_m3s }} <small>m³/s</small>
                  </div>
                  <span class="m-sub font-mono">Catchment Area: {{ inspection.parameters.catchment_area_ha }} ha</span>
                </div>

                <!-- Metric 4: Manning Capacity -->
                <div class="metric-card">
                  <span class="m-label">Manning Capacity (Qcap)</span>
                  <div class="m-val font-mono">
                    {{ inspection.parameters.full_capacity_m3s }} <small>m³/s</small>
                  </div>
                  <span class="m-sub font-mono">Roughness n = {{ inspection.parameters.manning_roughness_n }}</span>
                </div>
              </div>

              <!-- Hydraulic Dimensions & Elevation Breakdown -->
              <div class="specs-table-card">
                <span class="specs-title">Physical Conduit Geometry</span>
                <table class="specs-table font-mono">
                  <tbody>
                    <tr>
                      <td>Conduit Length</td>
                      <td>{{ inspection.parameters.conduit_length_m }} m</td>
                    </tr>
                    <tr>
                      <td>Cross Section (W × H)</td>
                      <td>{{ selectedEdge.width_m }}m × {{ selectedEdge.height_m }}m ({{ selectedEdge.shape }})</td>
                    </tr>
                    <tr>
                      <td>Bed Longitudinal Slope</td>
                      <td>{{ inspection.parameters.bed_slope_pct }}%</td>
                    </tr>
                    <tr>
                      <td>Water Velocity</td>
                      <td>{{ inspection.parameters.water_velocity_m_s }} m/s</td>
                    </tr>
                    <tr>
                      <td>Flow Depth vs Freeboard</td>
                      <td>{{ inspection.parameters.estimated_flow_depth_m }}m (Freeboard: {{ inspection.parameters.freeboard_m }}m)</td>
                    </tr>
                    <tr>
                      <td>Surcharge Pressure Head</td>
                      <td [class.text-danger]="inspection.parameters.surcharge_head_m > 0">
                        +{{ inspection.parameters.surcharge_head_m }} m above rim
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Connected Invert Nodes -->
              <div class="node-pair-card">
                <div class="node-item">
                  <span class="node-role">Source Node (Upstream):</span>
                  <span class="node-name">{{ inspection.source_node.name }}</span>
                  <span class="node-elev font-mono">Surface: {{ inspection.source_node.surface_elevation_m }}m | Invert: {{ inspection.source_node.invert_elevation_m }}m MSL</span>
                </div>
                <div class="node-divider">↓ Gravity Flow Direction</div>
                <div class="node-item">
                  <span class="node-role">Target Node (Downstream):</span>
                  <span class="node-name">{{ inspection.target_node.name }}</span>
                  <span class="node-elev font-mono">Surface: {{ inspection.target_node.surface_elevation_m }}m | Invert: {{ inspection.target_node.invert_elevation_m }}m MSL</span>
                </div>
              </div>
            </div>
          } @else {
            <div class="empty-inspector-state">
              <div class="empty-icon">🌊</div>
              <h3>Select a Drainage Conduit</h3>
              <p>Click any conduit line on the map or 3D viewport to inspect its Manning conveyance capacity and surface overflow risk.</p>
              <button class="btn-select-default" (click)="selectDefaultPipe()">
                Inspect Mithi River BKC Reach →
              </button>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .drainage-page {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      min-height: calc(100vh - 100px);
    }

    /* Header */
    .drainage-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 1rem 1.25rem;
    }
    .header-badge-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      flex-wrap: wrap;
      margin-bottom: 0.35rem;
    }
    .page-title {
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0;
    }
    .badge-status-3d {
      background: rgba(6, 182, 212, 0.15);
      color: #06b6d4;
      border: 1px solid rgba(6, 182, 212, 0.3);
      font-size: 0.68rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-sm);
      letter-spacing: 0.04em;
    }
    .badge-crs {
      background: var(--bg-darkest);
      color: var(--text-dim);
      border: 1px solid var(--border-light);
      font-size: 0.68rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-sm);
    }
    .page-subtitle {
      font-size: 0.8125rem;
      color: var(--text-muted);
      margin: 0;
      max-width: 800px;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .view-mode-tabs {
      display: flex;
      background: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.2rem;
      gap: 0.2rem;
    }
    .tab-btn {
      padding: 0.35rem 0.75rem;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      transition: all var(--transition-fast);
      &.active {
        background: var(--brand-primary);
        color: #ffffff;
      }
    }
    .view-controls {
      display: flex;
      gap: 0.4rem;
    }
    .btn-ctrl {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.65rem;
      background: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      color: var(--text-main);
      font-size: 0.75rem;
      font-weight: 600;
      transition: all var(--transition-fast);
      &:hover {
        border-color: #06b6d4;
        color: #06b6d4;
      }
    }

    /* Main Layout */
    .drainage-layout {
      display: grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 1.25rem;
      align-items: stretch;
      @media (max-width: 1200px) {
        grid-template-columns: 1fr;
      }
    }

    /* Viewport Card */
    .viewport-card {
      position: relative;
      background: #020617;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
      min-height: 640px;
      display: flex;
      flex-direction: column;
    }
    .leaflet-container-wrap {
      width: 100%;
      height: 100%;
      min-height: 640px;
      flex: 1;
    }
    .drainage-leaflet-canvas {
      width: 100%;
      height: 100%;
      min-height: 640px;
      background: #020617;
    }
    .canvas-container {
      width: 100%;
      height: 100%;
      min-height: 640px;
      flex: 1;
      cursor: grab;
      &:active { cursor: grabbing; }
    }
    canvas {
      display: block;
      width: 100%;
      height: 100%;
    }

    /* HUD */
    .canvas-hud {
      position: absolute;
      top: 0.75rem;
      left: 0.75rem;
      display: flex;
      align-items: center;
      background: rgba(2, 6, 23, 0.85);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: var(--radius-sm);
      padding: 0.4rem 0.75rem;
      gap: 0.75rem;
      z-index: 500;
      pointer-events: none;
    }
    .hud-item {
      display: flex;
      flex-direction: column;
    }
    .hud-label {
      font-size: 0.58rem;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .hud-val {
      font-size: 0.78rem;
      font-weight: 700;
      color: #ffffff;
    }
    .highlight-name {
      color: #38bdf8;
      max-width: 160px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .hud-divider {
      width: 1px;
      height: 20px;
      background: rgba(255, 255, 255, 0.1);
    }

    /* Legend */
    .canvas-legend {
      position: absolute;
      bottom: 2.5rem;
      left: 0.75rem;
      background: rgba(2, 6, 23, 0.88);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: var(--radius-sm);
      padding: 0.5rem 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      z-index: 500;
      pointer-events: none;
    }
    .leg-title {
      font-size: 0.62rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 0.15rem;
    }
    .leg-item {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.68rem;
      color: #e2e8f0;
    }
    .leg-dot {
      width: 10px;
      height: 10px;
      border-radius: 2px;
      flex-shrink: 0;
    }
    .leg-dot.underflow { background: #10b981; }
    .leg-dot.transition { background: #f59e0b; }
    .leg-dot.overflow { background: #ef4444; }
    .leg-dot.node-dot {
      border-radius: 50%;
      background: #06b6d4;
      border: 1px solid #ffffff;
    }

    .viewport-footer-hint {
      position: absolute;
      bottom: 0.5rem;
      left: 0.75rem;
      right: 0.75rem;
      font-size: 0.68rem;
      color: #94a3b8;
      background: rgba(2, 6, 23, 0.7);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      z-index: 500;
      pointer-events: none;
    }

    /* Inspector Card */
    .inspector-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .inspector-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border-light);
      background: var(--bg-card-subtle);
    }
    .inspector-label {
      font-size: 0.65rem;
      color: var(--text-dim);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .inspector-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0.1rem 0 0;
    }
    .pill-solver {
      font-size: 0.65rem;
      background: rgba(6, 182, 212, 0.15);
      color: #06b6d4;
      border: 1px solid rgba(6, 182, 212, 0.3);
      padding: 0.2rem 0.5rem;
      border-radius: var(--radius-sm);
      font-weight: 700;
    }

    .inspector-body {
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      overflow-y: auto;
      max-height: calc(100vh - 200px);
    }

    /* Conduit Badge */
    .conduit-badge-card {
      background: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.75rem 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .conduit-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.68rem;
    }
    .c-type { color: #06b6d4; font-weight: 700; }
    .c-id { color: var(--text-dim); }
    .c-name {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0.15rem 0 0;
    }
    .c-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin: 0;
    }

    /* Param Slider */
    .param-control-card {
      background: var(--bg-card-subtle);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.75rem 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .param-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .p-title { font-size: 0.72rem; font-weight: 700; color: var(--text-main); }
    .p-value { font-size: 0.85rem; font-weight: 800; color: #38bdf8; }
    .rainfall-slider {
      width: 100%;
      accent-color: #38bdf8;
      cursor: pointer;
    }
    .slider-presets {
      display: flex;
      gap: 0.35rem;
      flex-wrap: wrap;
    }
    .slider-presets button {
      background: var(--bg-darkest);
      border: 1px solid var(--border-light);
      color: var(--text-muted);
      font-size: 0.65rem;
      padding: 0.2rem 0.45rem;
      border-radius: 3px;
      cursor: pointer;
      &:hover { color: #38bdf8; border-color: #38bdf8; }
    }

    /* Verdict */
    .verdict-card {
      display: flex;
      gap: 0.65rem;
      padding: 0.75rem 0.85rem;
      border-radius: var(--radius-sm);
      border: 1px solid transparent;
      &.safe { background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.3); }
      &.alert { background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); }
      &.critical { background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.35); }
    }
    .verdict-icon { font-size: 1.1rem; }
    .verdict-title {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
    }
    .verdict-card.safe .verdict-title { color: #10b981; }
    .verdict-card.alert .verdict-title { color: #f59e0b; }
    .verdict-card.critical .verdict-title { color: #ef4444; }
    .verdict-desc {
      font-size: 0.75rem;
      color: var(--text-main);
      margin: 0.2rem 0 0;
      line-height: 1.35;
    }

    /* Metrics */
    .metrics-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.65rem;
    }
    .metric-card {
      background: var(--bg-card-subtle);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.65rem 0.75rem;
      display: flex;
      flex-direction: column;
    }
    .m-label { font-size: 0.62rem; color: var(--text-dim); text-transform: uppercase; }
    .m-val { font-size: 1.1rem; font-weight: 800; color: var(--text-main); margin: 0.15rem 0; }
    .m-val small { font-size: 0.7rem; font-weight: 500; color: var(--text-muted); }
    .m-sub { font-size: 0.62rem; color: var(--text-muted); }
    .util-bar {
      width: 100%;
      height: 4px;
      background: #1e293b;
      border-radius: 2px;
      margin: 0.25rem 0;
      overflow: hidden;
    }
    .util-fill { height: 100%; }
    .util-fill.safe { background: #10b981; }
    .util-fill.alert { background: #f59e0b; }
    .util-fill.critical { background: #ef4444; }

    /* Specs Table */
    .specs-table-card {
      background: var(--bg-darkest);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-sm);
      padding: 0.75rem 0.85rem;
    }
    .specs-title {
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-bottom: 0.4rem;
      display: block;
    }
    .specs-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.72rem;
    }
    .specs-table td {
      padding: 0.3rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-muted);
    }
    .specs-table td:last-child {
      text-align: right;
      font-weight: 600;
      color: var(--text-main);
    }

    /* Node Pair */
    .node-pair-card {
      background: rgba(6, 182, 212, 0.04);
      border: 1px solid rgba(6, 182, 212, 0.2);
      border-radius: var(--radius-sm);
      padding: 0.75rem 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .node-role { font-size: 0.62rem; color: #06b6d4; font-weight: 700; }
    .node-name { font-size: 0.78rem; font-weight: 700; color: var(--text-main); }
    .node-elev { font-size: 0.65rem; color: var(--text-dim); }
    .node-divider { text-align: center; color: #06b6d4; font-size: 0.75rem; }

    /* Empty State */
    .empty-inspector-state {
      padding: 3rem 1.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 0.75rem;
    }
    .empty-icon { font-size: 2.5rem; }
    .empty-inspector-state h3 { font-size: 1.05rem; color: var(--text-main); margin: 0; }
    .empty-inspector-state p { font-size: 0.78rem; color: var(--text-muted); max-width: 260px; margin: 0; }
    .btn-select-default {
      margin-top: 0.5rem;
      background: #06b6d4;
      color: #050811;
      font-weight: 700;
      font-size: 0.75rem;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: background var(--transition-fast);
      &:hover { background: #38bdf8; }
    }
  `]
})
export class DrainageComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('canvasRef', { static: false }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('containerRef', { static: false }) containerRef!: ElementRef<HTMLDivElement>;
  @ViewChild('gisMapRef', { static: false }) gisMapRef!: ElementRef<HTMLDivElement>;

  viewMode: 'GIS_MAP' | '3D_ISOMETRIC' = 'GIS_MAP';

  // Authentic Greater Mumbai Drainage Graph (BRIMSTOWAD)
  nodes: DrainageNode3D[] = [
    { id: 'NODE-MITHI-01', name: 'Vihar Lake Overflow Sluice', type: 'INLET_SUMP', basin: 'Mithi River Basin', lat: 19.1450, lon: 72.9050, surface_elevation_m: 24.5, invert_elevation_m: 21.0, depth_m: 3.5, description: 'Vihar Lake natural overflow channel and headwaters of Mithi River' },
    { id: 'NODE-MITHI-02', name: 'Powai - Saki Naka Confluence', type: 'JUNCTION', basin: 'Mithi River Basin', lat: 19.1100, lon: 72.8850, surface_elevation_m: 14.2, invert_elevation_m: 10.5, depth_m: 3.7, description: 'Industrial stormwater collector and airport perimeter channel' },
    { id: 'NODE-MITHI-03', name: 'Kurla CST Road Gauging Station', type: 'JUNCTION', basin: 'Mithi River Basin', lat: 19.0700, lon: 72.8700, surface_elevation_m: 5.8, invert_elevation_m: 2.4, depth_m: 3.4, description: 'Chronic constriction neck near Kurla railway terminus' },
    { id: 'NODE-MITHI-04', name: 'BKC Dharavi Tidal Estuary', type: 'JUNCTION', basin: 'Mithi River Basin', lat: 19.0550, lon: 72.8550, surface_elevation_m: 3.5, invert_elevation_m: 0.8, depth_m: 2.7, description: 'Tidal mudflats confluence with Sion-Bandra link road culverts' },
    { id: 'NODE-MITHI-OUTFALL', name: 'Mahim Causeway Bay Outfall', type: 'OUTFALL', basin: 'Mithi River Basin', lat: 19.0400, lon: 72.8380, surface_elevation_m: 2.0, invert_elevation_m: 0.0, depth_m: 2.0, description: 'Mahim Bay ocean outfall with BRIMSTOWAD tidal flap gates' },
    { id: 'NODE-HINDMATA-01', name: 'Hindmata Bowl Storm Sump', type: 'INLET_SUMP', basin: 'Island City Central', lat: 19.0080, lon: 72.8430, surface_elevation_m: 2.8, invert_elevation_m: 0.5, depth_m: 2.3, description: 'Saucer depression interceptor connected to underground holding tanks' },
    { id: 'NODE-BRITANNIA-PUMP', name: 'Britannia Stormwater Pumping Station', type: 'JUNCTION', basin: 'BRIMSTOWAD South', lat: 18.9720, lon: 72.8480, surface_elevation_m: 3.2, invert_elevation_m: 0.4, depth_m: 2.8, description: 'Reay Road high-capacity dewatering station (6 x 6000 m3/h pumps)' },
    { id: 'NODE-BRITANNIA-OUTFALL', name: 'Reay Road Harbour Outfall', type: 'OUTFALL', basin: 'BRIMSTOWAD South', lat: 18.9680, lon: 72.8550, surface_elevation_m: 1.8, invert_elevation_m: 0.0, depth_m: 1.8, description: 'Direct ocean discharge into Mumbai Harbour' },
    { id: 'NODE-LOVEGROVE-PUMP', name: 'Lovegrove Stormwater Pumping Station', type: 'JUNCTION', basin: 'BRIMSTOWAD West', lat: 19.0020, lon: 72.8180, surface_elevation_m: 2.5, invert_elevation_m: 0.2, depth_m: 2.3, description: 'Worli Naka pumping station discharging to Arabian Sea' },
    { id: 'NODE-LOVEGROVE-OUTFALL', name: 'Worli Sea Face Marine Outfall', type: 'OUTFALL', basin: 'BRIMSTOWAD West', lat: 19.0060, lon: 72.8120, surface_elevation_m: 1.5, invert_elevation_m: 0.0, depth_m: 1.5, description: 'High-volume marine outfall with anti-backflow sluice gates' },
    { id: 'NODE-ANDHERI-SUBWAY', name: 'Andheri Subway Inundation Sump', type: 'INLET_SUMP', basin: 'Western Suburbs Mid', lat: 19.1197, lon: 72.8464, surface_elevation_m: 2.4, invert_elevation_m: 0.1, depth_m: 2.3, description: 'Railway underpass low point equipped with continuous dewatering' },
    { id: 'NODE-MOGRA-01', name: 'Mogra Nullah Macro Drain', type: 'MACRO_CANAL', basin: 'Western Suburbs Mid', lat: 19.1250, lon: 72.8350, surface_elevation_m: 4.8, invert_elevation_m: 2.2, depth_m: 2.6, description: 'Open stormwater macro collector draining Andheri West' },
    { id: 'NODE-OSHIWARA-01', name: 'Aarey Colony Western Drainage Reach', type: 'JUNCTION', basin: 'Oshiwara Basin', lat: 19.1550, lon: 72.8750, surface_elevation_m: 18.5, invert_elevation_m: 15.0, depth_m: 3.5, description: 'Forested runoff collector into Oshiwara River' },
    { id: 'NODE-OSHIWARA-OUTFALL', name: 'Oshiwara River Malad Creek Outfall', type: 'OUTFALL', basin: 'Oshiwara Basin', lat: 19.1450, lon: 72.8250, surface_elevation_m: 2.1, invert_elevation_m: 0.0, depth_m: 2.1, description: 'Tidal discharge into Malad Creek and Arabian Sea' },
    { id: 'NODE-POISAR-01', name: 'Kandivali Poisar River Gauging Point', type: 'JUNCTION', basin: 'Poisar Basin', lat: 19.2050, lon: 72.8550, surface_elevation_m: 8.5, invert_elevation_m: 5.5, depth_m: 3.0, description: 'Suburban macro drain intercepting SV Road runoff' },
    { id: 'NODE-POISAR-OUTFALL', name: 'Poisar River Marve Creek Outfall', type: 'OUTFALL', basin: 'Poisar Basin', lat: 19.2150, lon: 72.8250, surface_elevation_m: 1.9, invert_elevation_m: 0.0, depth_m: 1.9, description: 'Ocean discharge at Marve Creek' },
    { id: 'NODE-DAHISAR-01', name: 'Borivali National Park Stream Sump', type: 'INLET_SUMP', basin: 'Dahisar Basin', lat: 19.2350, lon: 72.8900, surface_elevation_m: 22.0, invert_elevation_m: 18.5, depth_m: 3.5, description: 'Sanjay Gandhi National Park pristine hillside stream inflow' },
    { id: 'NODE-DAHISAR-OUTFALL', name: 'Dahisar River Manori Creek Outfall', type: 'OUTFALL', basin: 'Dahisar Basin', lat: 19.2500, lon: 72.8400, surface_elevation_m: 2.0, invert_elevation_m: 0.0, depth_m: 2.0, description: 'Northern boundary tidal estuary outfall' }
  ];

  edges: DrainageEdge3D[] = [
    { id: 'PIPE-MITHI-UPPER', name: 'Mithi River Upper Reach (Vihar to Powai)', type: 'RIVER_CHANNEL', source_node: 'NODE-MITHI-01', target_node: 'NODE-MITHI-02', length_m: 4800.0, width_m: 35.0, height_m: 3.8, shape: 'TRAPEZOIDAL', manning_n: 0.035, slope: 0.00215, manning_capacity_m3s: 260.0, catchment_area_ha: 2800.0, runoff_coeff: 0.72 },
    { id: 'PIPE-MITHI-MID', name: 'Mithi River Mid Reach (Saki Naka to Kurla)', type: 'RIVER_CHANNEL', source_node: 'NODE-MITHI-02', target_node: 'NODE-MITHI-03', length_m: 4200.0, width_m: 45.0, height_m: 3.6, shape: 'TRAPEZOIDAL', manning_n: 0.033, slope: 0.00120, manning_capacity_m3s: 295.0, catchment_area_ha: 3100.0, runoff_coeff: 0.88 },
    { id: 'PIPE-MITHI-BKC', name: 'Mithi River BKC Dharavi Choke Reach', type: 'RIVER_CHANNEL', source_node: 'NODE-MITHI-03', target_node: 'NODE-MITHI-04', length_m: 2600.0, width_m: 60.0, height_m: 3.2, shape: 'TRAPEZOIDAL', manning_n: 0.030, slope: 0.00065, manning_capacity_m3s: 320.0, catchment_area_ha: 1900.0, runoff_coeff: 0.92 },
    { id: 'PIPE-MITHI-ESTUARY', name: 'Mithi River to Mahim Causeway Outfall', type: 'RIVER_CHANNEL', source_node: 'NODE-MITHI-04', target_node: 'NODE-MITHI-OUTFALL', length_m: 2100.0, width_m: 85.0, height_m: 3.0, shape: 'TRAPEZOIDAL', manning_n: 0.028, slope: 0.00045, manning_capacity_m3s: 390.0, catchment_area_ha: 1400.0, runoff_coeff: 0.85 },
    { id: 'PIPE-HINDMATA-BRITANNIA', name: 'Hindmata to Britannia Station Box Culvert', type: 'STORM_WATER_DRAIN', source_node: 'NODE-HINDMATA-01', target_node: 'NODE-BRITANNIA-PUMP', length_m: 4100.0, width_m: 4.5, height_m: 2.6, shape: 'RECTANGULAR_BOX', manning_n: 0.015, slope: 0.00055, manning_capacity_m3s: 28.5, catchment_area_ha: 520.0, runoff_coeff: 0.95 },
    { id: 'PIPE-BRITANNIA-DISCHARGE', name: 'Britannia Pump Discharge to Harbour', type: 'MACRO_CANAL', source_node: 'NODE-BRITANNIA-PUMP', target_node: 'NODE-BRITANNIA-OUTFALL', length_m: 850.0, width_m: 8.0, height_m: 2.5, shape: 'RECTANGULAR_BOX', manning_n: 0.016, slope: 0.00165, manning_capacity_m3s: 36.0, catchment_area_ha: 180.0, runoff_coeff: 0.90 },
    { id: 'PIPE-LOVEGROVE-DISCHARGE', name: 'Lovegrove Pump to Worli Outfall', type: 'MACRO_CANAL', source_node: 'NODE-LOVEGROVE-PUMP', target_node: 'NODE-LOVEGROVE-OUTFALL', length_m: 650.0, width_m: 7.5, height_m: 2.4, shape: 'RECTANGULAR_BOX', manning_n: 0.016, slope: 0.00150, manning_capacity_m3s: 32.0, catchment_area_ha: 150.0, runoff_coeff: 0.92 },
    { id: 'PIPE-ANDHERI-TO-MOGRA', name: 'Andheri Subway Sump to Mogra Nullah', type: 'STORM_WATER_DRAIN', source_node: 'NODE-ANDHERI-SUBWAY', target_node: 'NODE-MOGRA-01', length_m: 1250.0, width_m: 2.8, height_m: 2.0, shape: 'RECTANGULAR_BOX', manning_n: 0.015, slope: 0.00120, manning_capacity_m3s: 14.5, catchment_area_ha: 260.0, runoff_coeff: 0.94 },
    { id: 'PIPE-MOGRA-TO-OSHIWARA', name: 'Mogra Nullah to Oshiwara Outfall', type: 'MACRO_CANAL', source_node: 'NODE-MOGRA-01', target_node: 'NODE-OSHIWARA-OUTFALL', length_m: 2800.0, width_m: 14.0, height_m: 2.5, shape: 'RECTANGULAR_OPEN', manning_n: 0.024, slope: 0.00085, manning_capacity_m3s: 42.0, catchment_area_ha: 890.0, runoff_coeff: 0.88 },
    { id: 'PIPE-OSHIWARA-MAIN', name: 'Oshiwara River Aarey Reach to Creek Outfall', type: 'RIVER_CHANNEL', source_node: 'NODE-OSHIWARA-01', target_node: 'NODE-OSHIWARA-OUTFALL', length_m: 5400.0, width_m: 32.0, height_m: 3.2, shape: 'TRAPEZOIDAL', manning_n: 0.032, slope: 0.00185, manning_capacity_m3s: 195.0, catchment_area_ha: 2400.0, runoff_coeff: 0.82 },
    { id: 'PIPE-POISAR-MAIN', name: 'Poisar River Suburban Channel to Marve Creek', type: 'RIVER_CHANNEL', source_node: 'NODE-POISAR-01', target_node: 'NODE-POISAR-OUTFALL', length_m: 3900.0, width_m: 26.0, height_m: 2.8, shape: 'TRAPEZOIDAL', manning_n: 0.031, slope: 0.00140, manning_capacity_m3s: 165.0, catchment_area_ha: 1850.0, runoff_coeff: 0.84 },
    { id: 'PIPE-DAHISAR-MAIN', name: 'Dahisar River National Park to Manori Creek', type: 'RIVER_CHANNEL', source_node: 'NODE-DAHISAR-01', target_node: 'NODE-DAHISAR-OUTFALL', length_m: 5900.0, width_m: 28.0, height_m: 3.0, shape: 'TRAPEZOIDAL', manning_n: 0.033, slope: 0.00220, manning_capacity_m3s: 185.0, catchment_area_ha: 2100.0, runoff_coeff: 0.78 }
  ];

  selectedEdge: DrainageEdge3D | null = null;
  inspection: HydraulicInspection | null = null;
  rainfallIntensity = 45.0; // mm/h
  zScale = 2.0;

  // Leaflet Map state
  private gisMap: L.Map | null = null;
  private gisPipesLayer = L.layerGroup();
  private gisNodesLayer = L.layerGroup();
  private pipePolylineMap = new Map<string, L.Polyline>();

  // 3D Canvas Engine state
  private rotX = 0.55;
  private rotY = -0.45;
  private zoom = 1.0;
  private panX = 0;
  private panY = 0;
  private isDragging = false;
  private lastMouseX = 0;
  private lastMouseY = 0;
  private animationFrameId = 0;
  private flowDashOffset = 0;

  bounds = {
    minLat: 18.89, maxLat: 19.30,
    minLon: 72.75, maxLon: 73.02,
    minElev: 0.0, maxElev: 28.5
  };

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.selectDefaultPipe();
    this.fetchBackendNetwork();
  }

  ngAfterViewInit(): void {
    // Initialize both viewports with safe timeouts
    setTimeout(() => {
      this.initGisMap();
      this.renderGisNetwork();
    }, 100);

    setTimeout(() => {
      if (this.canvasRef) {
        this.initCanvas3D();
      }
    }, 200);
  }

  ngOnDestroy(): void {
    if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
    if (this.gisMap) this.gisMap.remove();
  }

  switchViewMode(mode: 'GIS_MAP' | '3D_ISOMETRIC'): void {
    this.viewMode = mode;
    if (mode === 'GIS_MAP') {
      setTimeout(() => {
        if (this.gisMap) {
          this.gisMap.invalidateSize();
        } else {
          this.initGisMap();
          this.renderGisNetwork();
        }
      }, 50);
    } else {
      setTimeout(() => {
        if (!this.animationFrameId) {
          this.initCanvas3D();
        } else {
          this.resizeCanvas();
        }
      }, 50);
    }
  }

  fetchBackendNetwork(): void {
    this.http.get<any>(`${environment.apiBaseUrl}/api/v1/drainage/network-3d`).subscribe({
      next: (res) => {
        if (res && res.nodes && res.nodes.length > 0) {
          this.nodes = res.nodes;
        }
        if (res && (res.edges || res.links)) {
          this.edges = res.edges || res.links;
        }
        this.renderGisNetwork();
      },
      error: () => {
        // Fallback already initialized in class fields
      }
    });
  }

  selectDefaultPipe(): void {
    const defaultPipe = this.edges.find(e => e.id.includes('PIPE-MITHI-BKC')) || this.edges[0];
    if (defaultPipe) {
      this.selectEdge(defaultPipe);
    }
  }

  selectEdge(edge: DrainageEdge3D): void {
    this.selectedEdge = edge;
    this.computeInspection(edge, this.rainfallIntensity);
    this.highlightGisPipe(edge.id);
  }

  computeInspection(edge: DrainageEdge3D, rainfall: number): void {
    // Try backend inspect endpoint, fallback to local physical solver
    this.http.get<HydraulicInspection>(`${environment.apiBaseUrl}/api/v1/drainage/hydraulic-inspect?conduit_id=${edge.id}&rainfall_intensity_mm_h=${rainfall}`).subscribe({
      next: (res) => {
        this.inspection = res;
      },
      error: () => {
        this.inspection = this.solveLocalHydraulics(edge, rainfall);
      }
    });
  }

  solveLocalHydraulics(edge: DrainageEdge3D, rainfall: number): HydraulicInspection {
    const src = this.nodes.find(n => n.id === edge.source_node) || this.nodes[0];
    const tgt = this.nodes.find(n => n.id === edge.target_node) || this.nodes[1];

    // Rational Runoff Inflow: Q_in = 0.002778 * C * I * A
    const qInflow = 0.002778 * edge.runoff_coeff * rainfall * edge.catchment_area_ha;
    const qCap = edge.manning_capacity_m3s;
    const ratio = qInflow / qCap;

    let status: 'UNDERFLOW' | 'TRANSITION' | 'OVERFLOW_SURCHARGE' = 'UNDERFLOW';
    let severity: 'SAFE' | 'ALERT' | 'CRITICAL' = 'SAFE';
    let surcharge = 0.0;
    let head = 0.0;
    let verdict = 'Safe gravitational conveyance. Available freeboard prevents street waterlogging.';

    if (ratio < 0.75) {
      status = 'UNDERFLOW';
      severity = 'SAFE';
    } else if (ratio <= 1.0) {
      status = 'TRANSITION';
      severity = 'ALERT';
      verdict = 'Conduit operating near full-barrel design capacity. Surcharge imminent if rainfall peaks.';
    } else {
      status = 'OVERFLOW_SURCHARGE';
      severity = 'CRITICAL';
      surcharge = Math.round((qInflow - qCap) * 100) / 100;
      head = Math.min(1.8, Math.round((surcharge / (edge.width_m * 2.0)) * 100) / 100);
      verdict = `Hydraulic capacity exceeded! Surcharging manhole rims at ${surcharge} m³/s onto street surface.`;
    }

    const flowDepth = ratio < 1.0 ? Math.round(edge.height_m * ratio * 100) / 100 : edge.height_m;

    return {
      pipe_id: edge.id,
      pipe_name: edge.name,
      pipe_type: edge.type,
      source_node: src,
      target_node: tgt,
      hydraulic_status: status,
      severity_level: severity,
      parameters: {
        rainfall_intensity_mm_h: rainfall,
        catchment_area_ha: edge.catchment_area_ha,
        runoff_coefficient: edge.runoff_coeff,
        conduit_length_m: edge.length_m,
        bed_slope_pct: Math.round(edge.slope * 1000) / 10,
        manning_roughness_n: edge.manning_n,
        cross_sectional_area_m2: Math.round(edge.width_m * edge.height_m * 10) / 10,
        hydraulic_radius_m: Math.round((edge.width_m * edge.height_m) / (edge.width_m + 2 * edge.height_m) * 100) / 100,
        full_capacity_m3s: Math.round(qCap * 10) / 10,
        inflow_discharge_m3s: Math.round(qInflow * 10) / 10,
        capacity_utilization_pct: Math.round(ratio * 100),
        water_velocity_m_s: Math.round((qInflow / Math.max(1, edge.width_m * flowDepth)) * 100) / 100,
        estimated_flow_depth_m: flowDepth,
        surcharge_rate_m3s: surcharge,
        surcharge_head_m: head,
        freeboard_m: Math.max(0, Math.round((edge.height_m - flowDepth) * 100) / 100)
      },
      engineering_verdict: verdict,
      timestamp: new Date().toISOString()
    };
  }

  onRainfallChange(): void {
    if (this.selectedEdge) {
      this.computeInspection(this.selectedEdge, this.rainfallIntensity);
    }
    // Update pipe line colors dynamically on the map based on new rainfall
    this.renderGisNetwork();
  }

  setPresetRainfall(val: number): void {
    this.rainfallIntensity = val;
    this.onRainfallChange();
  }

  mathMin(a: number, b: number): number {
    return Math.min(a, b);
  }

  // --------------------------------------------------------------------------
  // GIS Leaflet Map Engine
  // --------------------------------------------------------------------------
  private initGisMap(): void {
    if (!this.gisMapRef || this.gisMap) return;

    this.gisMap = L.map(this.gisMapRef.nativeElement, {
      center: [19.0760, 72.8777],
      zoom: 12,
      zoomControl: true,
      preferCanvas: true
    });

    // High-contrast Dark Carto basemap
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 18,
      subdomains: ['a', 'b', 'c'],
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(this.gisMap);

    this.gisPipesLayer.addTo(this.gisMap);
    this.gisNodesLayer.addTo(this.gisMap);

    setTimeout(() => {
      this.gisMap?.invalidateSize();
    }, 150);
  }

  private renderGisNetwork(): void {
    if (!this.gisMap) return;

    this.gisPipesLayer.clearLayers();
    this.gisNodesLayer.clearLayers();
    this.pipePolylineMap.clear();

    const nodeMap = new Map(this.nodes.map(n => [n.id, n]));

    // Render Conduits / Pipes
    this.edges.forEach(edge => {
      const src = nodeMap.get(edge.source_node);
      const tgt = nodeMap.get(edge.target_node);
      if (!src || !tgt) return;

      // Determine real-time hydraulic status under current rainfall
      const qInflow = 0.002778 * edge.runoff_coeff * this.rainfallIntensity * edge.catchment_area_ha;
      const ratio = qInflow / edge.manning_capacity_m3s;

      let color = '#10b981'; // Green (Underflow)
      let statusText = 'UNDERFLOW (SAFE)';
      let weight = Math.max(4, Math.min(9, edge.width_m / 6));

      if (ratio > 1.0) {
        color = '#ef4444'; // Red (Surcharge Overflow)
        statusText = 'OVERFLOW SURCHARGE (CRITICAL)';
        weight += 2;
      } else if (ratio >= 0.75) {
        color = '#f59e0b'; // Amber (Transition)
        statusText = 'TRANSITION (ALERT)';
      }

      const isSelected = this.selectedEdge?.id === edge.id;
      if (isSelected) {
        // Render glowing cyan outline underneath
        const halo = L.polyline([[src.lat, src.lon], [tgt.lat, tgt.lon]], {
          color: '#38bdf8',
          weight: weight + 6,
          opacity: 0.8
        });
        this.gisPipesLayer.addLayer(halo);
      }

      const poly = L.polyline([[src.lat, src.lon], [tgt.lat, tgt.lon]], {
        color: color,
        weight: weight,
        opacity: 0.95
      });

      poly.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px; color: #0f172a; padding: 2px;">
          <strong style="color: #0284c7;">${edge.name}</strong><br/>
          <span>Type: <strong>${edge.type}</strong></span><br/>
          <span>Status: <strong style="color: ${color};">${statusText}</strong></span><br/>
          <span>Inflow: <strong>${Math.round(qInflow * 10) / 10} m³/s</strong> | Cap: <strong>${edge.manning_capacity_m3s} m³/s</strong></span><br/>
          <span style="color: #059669; font-weight: bold;">⚡ Click to inspect Manning hydraulics</span>
        </div>
      `, { sticky: true });

      poly.on('click', () => {
        this.selectEdge(edge);
      });

      this.gisPipesLayer.addLayer(poly);
      this.pipePolylineMap.set(edge.id, poly);
    });

    // Render Junction & Outfall Nodes
    this.nodes.forEach(node => {
      let iconColor = '#06b6d4';
      let iconLabel = '⚙️';
      if (node.type === 'OUTFALL') {
        iconColor = '#3b82f6';
        iconLabel = '🌊';
      } else if (node.type === 'INLET_SUMP') {
        iconColor = '#10b981';
        iconLabel = '📥';
      }

      const customIcon = L.divIcon({
        className: 'drainage-gis-node',
        html: `
          <div style="background: ${iconColor}; border: 2px solid #ffffff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; box-shadow: 0 0 8px ${iconColor}; cursor: pointer;">
            ${iconLabel}
          </div>
          <div style="background: rgba(15,23,42,0.9); color: #38bdf8; font-family: monospace; font-size: 9px; font-weight: bold; border-radius: 3px; padding: 1px 3px; margin-top: 2px; white-space: nowrap; border: 1px solid rgba(56,189,248,0.3);">
            +${node.surface_elevation_m}m
          </div>
        `,
        iconSize: [24, 38],
        iconAnchor: [12, 12]
      });

      const marker = L.marker([node.lat, node.lon], { icon: customIcon });
      marker.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px; color: #0f172a;">
          <strong style="color: #0284c7;">${node.name}</strong><br/>
          <span>Type: <strong>${node.type}</strong> (${node.basin})</span><br/>
          <span>Surface Elevation: <strong>${node.surface_elevation_m} m MSL</strong></span><br/>
          <span>Invert Elevation: <strong>${node.invert_elevation_m} m MSL</strong></span><br/>
          <span style="color: #64748b;">${node.description}</span>
        </div>
      `);

      this.gisNodesLayer.addLayer(marker);
    });
  }

  private highlightGisPipe(pipeId: string): void {
    if (!this.gisMap) return;
    this.renderGisNetwork();
  }

  // --------------------------------------------------------------------------
  // 3D Isometric Viewport Engine (WebGL / 2D Canvas)
  // --------------------------------------------------------------------------
  private initCanvas3D(): void {
    this.resizeCanvas();
    this.renderLoop();
  }

  @HostListener('window:resize')
  resizeCanvas(): void {
    if (!this.canvasRef || !this.containerRef) return;
    const canvas = this.canvasRef.nativeElement;
    const rect = this.containerRef.nativeElement.getBoundingClientRect();
    canvas.width = rect.width * (window.devicePixelRatio || 1);
    canvas.height = rect.height * (window.devicePixelRatio || 1);
  }

  resetCamera(): void {
    this.rotX = 0.55;
    this.rotY = -0.45;
    this.zoom = 1.0;
    this.panX = 0;
    this.panY = 0;
  }

  setTopView(): void {
    this.rotX = 0.05;
    this.rotY = 0.0;
    this.zoom = 1.1;
  }

  toggleElevationExaggeration(): void {
    this.zScale = this.zScale === 2.0 ? 4.0 : this.zScale === 4.0 ? 1.0 : 2.0;
  }

  onMouseDown(e: MouseEvent): void {
    this.isDragging = true;
    this.lastMouseX = e.clientX;
    this.lastMouseY = e.clientY;
  }

  onMouseMove(e: MouseEvent): void {
    if (!this.isDragging) return;
    const dx = e.clientX - this.lastMouseX;
    const dy = e.clientY - this.lastMouseY;
    if (e.shiftKey || e.button === 1) {
      this.panX += dx;
      this.panY += dy;
    } else {
      this.rotY += dx * 0.008;
      this.rotX += dy * 0.008;
      this.rotX = Math.max(0.05, Math.min(Math.PI / 2 - 0.05, this.rotX));
    }
    this.lastMouseX = e.clientX;
    this.lastMouseY = e.clientY;
  }

  onMouseUp(): void {
    this.isDragging = false;
  }

  onWheel(e: WheelEvent): void {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    this.zoom = Math.max(0.4, Math.min(3.5, this.zoom * zoomFactor));
  }

  onCanvasClick(e: MouseEvent): void {
    if (!this.canvasRef) return;
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Hit test pipes in 3D projection
    let closestPipe: DrainageEdge3D | null = null;
    let minD = 24;

    const nodeMap = new Map(this.nodes.map(n => [n.id, n]));

    this.edges.forEach(edge => {
      const src = nodeMap.get(edge.source_node);
      const tgt = nodeMap.get(edge.target_node);
      if (src && tgt && src.screenX !== undefined && tgt.screenX !== undefined) {
        const midX = (src.screenX + tgt.screenX) / 2;
        const midY = (src.screenY! + tgt.screenY!) / 2;
        const d = Math.hypot(clickX - midX, clickY - midY);
        if (d < minD) {
          minD = d;
          closestPipe = edge;
        }
      }
    });

    if (closestPipe) {
      this.selectEdge(closestPipe);
    }
  }

  private renderLoop(): void {
    this.flowDashOffset += 0.4;
    this.draw3DScene();
    this.animationFrameId = requestAnimationFrame(() => this.renderLoop());
  }

  private draw3DScene(): void {
    if (!this.canvasRef) return;
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    const cx = w / 2 + this.panX;
    const cy = h / 2 + this.panY;

    // 3D Projection Helper
    const project = (lat: number, lon: number, elev: number) => {
      const nx = (lon - this.bounds.minLon) / (this.bounds.maxLon - this.bounds.minLon) - 0.5;
      const ny = (lat - this.bounds.minLat) / (this.bounds.maxLat - this.bounds.minLat) - 0.5;
      const nz = (elev / this.bounds.maxElev) * 0.3 * this.zScale;

      const cosY = Math.cos(this.rotY);
      const sinY = Math.sin(this.rotY);
      const x1 = nx * cosY - ny * sinY;
      const y1 = nx * sinY + ny * cosY;

      const cosX = Math.cos(this.rotX);
      const sinX = Math.sin(this.rotX);
      const y2 = y1 * cosX - nz * sinX;
      const z2 = y1 * sinX + nz * cosX;

      const scale = 320 * this.zoom;
      return {
        x: cx + x1 * scale,
        y: cy - y2 * scale,
        depth: z2
      };
    };

    // Draw 3D Ground Grid
    ctx.strokeStyle = 'rgba(30, 41, 59, 0.45)';
    ctx.lineWidth = 1;
    const gridSteps = 8;
    for (let i = 0; i <= gridSteps; i++) {
      const f = i / gridSteps;
      const lon = this.bounds.minLon + f * (this.bounds.maxLon - this.bounds.minLon);
      const p1 = project(this.bounds.minLat, lon, 0);
      const p2 = project(this.bounds.maxLat, lon, 0);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();

      const lat = this.bounds.minLat + f * (this.bounds.maxLat - this.bounds.minLat);
      const p3 = project(lat, this.bounds.minLon, 0);
      const p4 = project(lat, this.bounds.maxLon, 0);
      ctx.beginPath();
      ctx.moveTo(p3.x, p3.y);
      ctx.lineTo(p4.x, p4.y);
      ctx.stroke();
    }

    // Update screen positions for nodes
    const nodeMap = new Map<string, DrainageNode3D>();
    this.nodes.forEach(node => {
      const pt = project(node.lat, node.lon, node.surface_elevation_m);
      node.screenX = pt.x;
      node.screenY = pt.y;
      nodeMap.set(node.id, node);

      // Draw vertical drop shaft to invert
      const invertPt = project(node.lat, node.lon, node.invert_elevation_m);
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.35)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(pt.x, pt.y);
      ctx.lineTo(invertPt.x, invertPt.y);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Draw Conduits (Pipes)
    this.edges.forEach(edge => {
      const src = nodeMap.get(edge.source_node);
      const tgt = nodeMap.get(edge.target_node);
      if (!src || !tgt || src.screenX === undefined || tgt.screenX === undefined) return;

      const qInflow = 0.002778 * edge.runoff_coeff * this.rainfallIntensity * edge.catchment_area_ha;
      const ratio = qInflow / edge.manning_capacity_m3s;

      let strokeColor = '#10b981';
      if (ratio > 1.0) strokeColor = '#ef4444';
      else if (ratio >= 0.75) strokeColor = '#f59e0b';

      const isSelected = this.selectedEdge?.id === edge.id;

      if (isSelected) {
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 8;
        ctx.beginPath();
        ctx.moveTo(src.screenX, src.screenY!);
        ctx.lineTo(tgt.screenX, tgt.screenY!);
        ctx.stroke();
      }

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = isSelected ? 4.5 : 3;
      ctx.beginPath();
      ctx.moveTo(src.screenX, src.screenY!);
      ctx.lineTo(tgt.screenX, tgt.screenY!);
      ctx.stroke();

      // Animated Water Flow Pulses
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 18]);
      ctx.lineDashOffset = -this.flowDashOffset;
      ctx.beginPath();
      ctx.moveTo(src.screenX, src.screenY!);
      ctx.lineTo(tgt.screenX, tgt.screenY!);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Draw Nodes (Manholes / Inlets)
    this.nodes.forEach(node => {
      if (node.screenX === undefined || node.screenY === undefined) return;
      const x = node.screenX;
      const y = node.screenY;

      ctx.fillStyle = node.type === 'OUTFALL' ? '#3b82f6' : node.type === 'INLET_SUMP' ? '#10b981' : '#06b6d4';
      ctx.beginPath();
      ctx.arc(x, y, 5.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#cbd5e1';
      ctx.font = '10px monospace';
      ctx.fillText(`+${node.surface_elevation_m}m`, x + 8, y + 3);
    });
  }
}
