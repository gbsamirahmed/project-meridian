import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

import {
  removeTemperatureLayer,
  updateTemperatureLayer,
} from "../services/temperatureLayer";

import {
  removeCloudLayer,
  updateCloudLayer,
} from "../services/cloudLayer";

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
      removeTemperatureLayer(map);
      removeCloudLayer(map);
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
      (selectedLayer === "temperature" || selectedLayer === "clouds") &&
      gridPoints.length > 0
    ) {
      const longitudes = gridPoints.map((point) => point.longitude);
      const latitudes = gridPoints.map((point) => point.latitude);

      const bounds = new maplibregl.LngLatBounds(
        [Math.min(...longitudes), Math.min(...latitudes)],
        [Math.max(...longitudes), Math.max(...latitudes)]
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
  }, [selectedLocation, selectedLayer, gridPoints]);

  useEffect(() => {
    if (!mapRef.current) return;

    removeTemperatureLayer(mapRef.current);
    removeCloudLayer(mapRef.current);

    if (gridPoints.length === 0) return;

    if (selectedLayer === "temperature") {
      updateTemperatureLayer(mapRef.current, gridPoints);
    }

    if (selectedLayer === "clouds") {
      updateCloudLayer(mapRef.current, gridPoints);
    }
  }, [gridPoints, selectedLayer]);

  return (
    <div className="map-container-wrapper">
      <div className="map-container" ref={mapContainer} />

      <div className="layer-badge">Layer: {selectedLayer}</div>
    </div>
  );
}