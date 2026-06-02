import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

import type { SelectedLocation } from "../types/location";
import type { WeatherLayer } from "../types/layer";
import type { GridPoint } from "../types/gridPoint";

import "maplibre-gl/dist/maplibre-gl.css";

interface MapViewProps {
  selectedLocation: SelectedLocation | null;
  selectedLayer: WeatherLayer;
  gridPoints: GridPoint[];
  onLocationSelect: (location: SelectedLocation) => void;
}

export default function MapView({
  selectedLocation,
  selectedLayer,
  gridPoints,
  onLocationSelect,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const gridMarkersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [-0.1276, 51.5072],
      zoom: 9,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("click", (event) => {
      onLocationSelect({
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [onLocationSelect]);

  useEffect(() => {
    if (!selectedLocation || !mapRef.current) return;

    const lngLat: [number, number] = [
      selectedLocation.longitude,
      selectedLocation.latitude,
    ];

    if (
      selectedLayer === "temperature" &&
      gridPoints.length > 0
    ) {
      const longitudes = gridPoints.map((p) => p.longitude);
      const latitudes = gridPoints.map((p) => p.latitude);

      const bounds = new maplibregl.LngLatBounds(
        [
          Math.min(...longitudes),
          Math.min(...latitudes),
        ],
        [
          Math.max(...longitudes),
          Math.max(...latitudes),
        ]
      );

      mapRef.current.fitBounds(bounds, {
        padding: 100,
        duration: 1000,
      });
    } else {
      mapRef.current.flyTo({
        center: lngLat,
        zoom: 10,
        essential: true,
      });
    }

    if (markerRef.current) {
      markerRef.current.setLngLat(lngLat);
    } else {
      markerRef.current = new maplibregl.Marker()
        .setLngLat(lngLat)
        .addTo(mapRef.current);
    }
  }, [
    selectedLocation,
    selectedLayer,
    gridPoints,
  ]);

  useEffect(() => {
    if (!mapRef.current) return;

    gridMarkersRef.current.forEach((marker) => marker.remove());
    gridMarkersRef.current = [];

    if (selectedLayer !== "temperature") return;
    if (gridPoints.length === 0) return;

    const temperatures = gridPoints.map(
      (p) => p.temperature
    );

    const minTemp = Math.min(...temperatures);
    const maxTemp = Math.max(...temperatures);

    gridPoints.forEach((point) => {
      const element = document.createElement("div");

      let ratio = 0.5;

      if (maxTemp !== minTemp) {
        ratio =
          (point.temperature - minTemp) /
          (maxTemp - minTemp);
      }

      const hue = 240 - ratio * 240;

      element.className = "temperature-marker";
      element.style.backgroundColor =
        `hsl(${hue}, 85%, 50%)`;

      element.textContent =
        `${Math.round(point.temperature)}°`;

      const marker = new maplibregl.Marker({
        element,
      })
        .setLngLat([
          point.longitude,
          point.latitude,
        ])
        .addTo(mapRef.current!);

      gridMarkersRef.current.push(marker);
    });
  }, [gridPoints, selectedLayer]);

  return (
    <div className="map-container-wrapper">
      <div
        className="map-container"
        ref={mapContainer}
      />

      <div className="layer-badge">
        Layer: {selectedLayer}
      </div>
    </div>
  );
}