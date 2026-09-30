"use client";

// Map adapter: Google Maps JavaScript API when NEXT_PUBLIC_MAPS_API_KEY is set, otherwise
// Leaflet + OpenStreetMap tiles (demo fallback). Both draw the same primitives.
import { useEffect, useRef, useState } from "react";

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";

export type LatLng = [number, number];
export type Style = { color: string; fill?: string; fillOpacity?: number; weight?: number; dash?: string; opacity?: number };
export type MapPoint = { lat: number; lon: number; radius: number; style: Style; tooltip: string; id?: string };
export type MapFeatures = {
  bounds: [LatLng, LatLng];
  images: { url: string; bounds: [LatLng, LatLng]; opacity: number }[];
  polygons: { latlngs: LatLng[]; style: Style }[];
  lines: { latlngs: LatLng[]; style: Style; tooltip?: string }[];
  points: MapPoint[];
  tileUrl?: string | null;
};

interface Driver {
  draw(f: MapFeatures, onClick: (id: string) => void): void;
  fit(b: [LatLng, LatLng]): void;
  destroy(): void;
}

async function leafletDriver(el: HTMLDivElement): Promise<Driver> {
  const L = (await import("leaflet")).default;
  const map = L.map(el, { zoomControl: true, attributionControl: true });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors (ODbL)",
  }).addTo(map);
  const group = L.layerGroup().addTo(map);
  return {
    draw(f, onClick) {
      group.clearLayers();
      if (f.tileUrl) L.tileLayer(f.tileUrl, { opacity: 0.8, attribution: "Google Earth Engine" }).addTo(group);
      for (const img of f.images) L.imageOverlay(img.url, img.bounds, { opacity: img.opacity }).addTo(group);
      for (const p of f.polygons)
        L.polygon(p.latlngs, { color: p.style.color, weight: p.style.weight ?? 1, fillColor: p.style.fill,
          fillOpacity: p.style.fillOpacity ?? 0.1, dashArray: p.style.dash, interactive: false }).addTo(group);
      for (const l of f.lines) {
        const pl = L.polyline(l.latlngs, { color: l.style.color, weight: l.style.weight ?? 2, dashArray: l.style.dash,
          opacity: l.style.opacity ?? 0.9 }).addTo(group);
        if (l.tooltip) pl.bindTooltip(l.tooltip, { sticky: true });
      }
      for (const p of f.points) {
        const m = L.circleMarker([p.lat, p.lon], { radius: p.radius, color: p.style.color, weight: p.style.weight ?? 1,
          fillColor: p.style.fill ?? p.style.color, fillOpacity: p.style.fillOpacity ?? 0.9, dashArray: p.style.dash }).addTo(group);
        m.bindTooltip(p.tooltip);
        if (p.id) m.on("click", () => onClick(p.id!));
      }
    },
    fit(b) {
      map.fitBounds(b);
    },
    destroy() {
      map.remove();
    },
  };
}

// Minimal typings for the parts of the Google Maps JS API we use (no extra dependency).
type GObj = { setMap(m: unknown): void; addListener?(ev: string, cb: () => void): void };
type GMaps = {
  Map: new (el: HTMLElement, opts: object) => { fitBounds(b: unknown): void };
  LatLngBounds: new (sw: object, ne: object) => unknown;
  GroundOverlay: new (url: string, b: unknown, o: object) => GObj;
  Polygon: new (o: object) => GObj;
  Polyline: new (o: object) => GObj;
  Marker: new (o: object) => GObj;
  InfoWindow: new () => { setContent(s: string): void; open(o: object): void; close(): void };
  SymbolPath: { CIRCLE: unknown };
};

function loadGoogle(): Promise<GMaps> {
  const w = window as unknown as { google?: { maps: GMaps } };
  if (w.google?.maps) return Promise.resolve(w.google.maps);
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(MAPS_KEY)}`;
    s.async = true;
    s.onload = () => (w.google?.maps ? resolve(w.google.maps) : reject(new Error("Google Maps failed to load")));
    s.onerror = () => reject(new Error("Google Maps failed to load"));
    document.head.appendChild(s);
  });
}

async function googleDriver(el: HTMLDivElement): Promise<Driver> {
  const g = await loadGoogle();
  const map = new g.Map(el, { mapTypeId: "terrain", streetViewControl: false, fullscreenControl: false });
  const info = new g.InfoWindow();
  let objs: GObj[] = [];
  const ll = (p: LatLng) => ({ lat: p[0], lng: p[1] });
  const bounds = (b: [LatLng, LatLng]) => new g.LatLngBounds(ll(b[0]), ll(b[1]));
  return {
    draw(f, onClick) {
      objs.forEach((o) => o.setMap(null));
      objs = [];
      for (const img of f.images) objs.push(new g.GroundOverlay(img.url, bounds(img.bounds), { opacity: img.opacity, clickable: false }));
      for (const p of f.polygons)
        objs.push(new g.Polygon({ paths: p.latlngs.map(ll), strokeColor: p.style.color, strokeWeight: p.style.weight ?? 1,
          fillColor: p.style.fill, fillOpacity: p.style.fillOpacity ?? 0.1, clickable: false }));
      for (const l of f.lines)
        objs.push(new g.Polyline({ path: l.latlngs.map(ll), strokeColor: l.style.color, strokeWeight: l.style.weight ?? 2,
          strokeOpacity: l.style.opacity ?? 0.9 }));
      for (const p of f.points) {
        const m = new g.Marker({ position: { lat: p.lat, lng: p.lon }, title: p.tooltip,
          icon: { path: g.SymbolPath.CIRCLE, scale: p.radius, fillColor: p.style.fill ?? p.style.color,
            fillOpacity: p.style.fillOpacity ?? 0.9, strokeColor: p.style.color, strokeWeight: p.style.weight ?? 1 } });
        m.addListener?.("click", () => {
          info.setContent(p.tooltip);
          info.open({ anchor: m });
          if (p.id) onClick(p.id);
        });
        objs.push(m);
      }
      objs.forEach((o) => o.setMap(map));
    },
    fit(b) {
      map.fitBounds(bounds(b));
    },
    destroy() {
      objs.forEach((o) => o.setMap(null));
    },
  };
}

export function HazardMap({ features, onSelect, height = 560 }: { features: MapFeatures | null; onSelect?: (id: string) => void; height?: number }) {
  const el = useRef<HTMLDivElement>(null);
  const driver = useRef<Driver | null>(null);
  const [ready, setReady] = useState(false);
  // Google reports key/referrer problems via window.gm_authFailure after the script has loaded; fall back then too.
  const [googleOk, setGoogleOk] = useState(Boolean(MAPS_KEY));
  const [provider, setProvider] = useState<string>(MAPS_KEY ? "Google Maps" : "Leaflet + OpenStreetMap (demo fallback)");
  const fitted = useRef<string>("");
  const onSelectRef = useRef(onSelect);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    let cancelled = false;
    const node = el.current;
    if (!node) return;
    const fallback = (why: string) => {
      setProvider(`Leaflet + OpenStreetMap (${why})`);
      node.innerHTML = "";
      return leafletDriver(node);
    };
    if (googleOk) {
      (window as unknown as { gm_authFailure?: () => void }).gm_authFailure = () => {
        if (!cancelled) setGoogleOk(false);
      };
    }
    const make = googleOk
      ? googleDriver(node).catch(() => fallback("Google Maps failed to load"))
      : MAPS_KEY ? fallback("Google Maps key not authorised for this URL") : leafletDriver(node);
    make.then((d) => {
      if (cancelled) {
        d.destroy();
        return;
      }
      driver.current = d;
      fitted.current = "";
      setReady(true);
    });
    return () => {
      cancelled = true;
      setReady(false);
      driver.current?.destroy();
      driver.current = null;
    };
  }, [googleOk]);

  useEffect(() => {
    if (!ready || !driver.current || !features) return;
    driver.current.draw(features, (id) => onSelectRef.current?.(id));
    const key = JSON.stringify(features.bounds);
    if (fitted.current !== key) {
      driver.current.fit(features.bounds);
      fitted.current = key;
    }
  }, [ready, features]);

  return (
    <div className="relative">
      <div ref={el} style={{ height }} className="w-full overflow-hidden rounded-lg border bg-muted" />
      <div className="pointer-events-none absolute bottom-1 left-1 z-[400] rounded bg-background/85 px-1.5 py-0.5 text-[10px] text-muted-foreground">
        Map: {provider}
      </div>
    </div>
  );
}

// ---- raster helpers -------------------------------------------------------------------------

export type RGBA = [number, number, number, number];

export function rasterUrl(grid: { rows: number; cols: number }, color: (i: number) => RGBA | null): string {
  const canvas = document.createElement("canvas");
  canvas.width = grid.cols;
  canvas.height = grid.rows;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";
  const img = ctx.createImageData(grid.cols, grid.rows);
  for (let i = 0; i < grid.rows * grid.cols; i++) {
    const c = color(i);
    if (!c) continue;
    img.data.set(c, i * 4);
  }
  ctx.putImageData(img, 0, 0);
  return canvas.toDataURL("image/png");
}
