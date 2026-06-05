import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";

import { removeTemperatureLayer } from "../services/temperatureLayer";
import { removeCloudLayer } from "../services/cloudLayer";
import { removePrecipitationLayer } from "../services/precipitationLayer";

import {
  removePressureLayer,
  updatePressureLayer,
} from "../services/pressureLayer";

import {
  removeWindLayer,
  updateWindLayer,
} from "../services/windLayer";

import {
  removeRasterLayer,
  updateRasterLayer,
} from "../services/rasterLayer";

import {
  removeCloudRasterLayer,
  updateCloudRasterLayer,
} from "../services/cloudRasterLayer";

import {
  removePrecipitationRasterLayer,
  updatePrecipitationRasterLayer,
} from "../services/precipitationRasterLayer";

import {
  removeElevationRasterLayer,
  updateElevationRasterLayer,
} from "../services/elevationRasterLayer";

import {
  removeHillshadeRasterLayer,
  updateHillshadeRasterLayer,
} from "../services/hillshadeRasterLayer";

import { getGridCoordinates } from "../services/gridCoordinates";
import { interpolateGridValue } from "../services/interpolation";
import { buildWeatherMatrix } from "../services/weatherMatrix";

import { GRID_SIZE } from "../config/gridConfig";

import type { SelectedLocation } from "../types/location";
import type { WeatherLayer } from "../types/layer";
import type { GridPoint } from "../types/gridPoint";

import "maplibre-gl/dist/maplibre-gl.css";

interface MapViewProps {
  selectedLocation: SelectedLocation | null;
  selectedLayer: WeatherLayer;
  gridPoints: GridPoint[];
  forecastHour: number;
  mapPitch: number;
  overlayOpacity: number;
  onLocationSelect: (location: SelectedLocation) => void;
}

interface HoverInfo {
  x: number;
  y: number;
  elevation: number;
  temperature: number;
  cloudCover: number;
  precipitation: number;
  pressure: number;
  windSpeed: number;
}

function isInsideGridBounds(
  latitude: number,
  longitude: number,
  gridPoints: GridPoint[]
): boolean {
  if (gridPoints.length === 0) return false;

  const longitudes = gridPoints.map((point) => point.longitude);
  const latitudes = gridPoints.map((point) => point.latitude);

  const west = Math.min(...longitudes);
  const east = Math.max(...longitudes);
  const south = Math.min(...latitudes);
  const north = Math.max(...latitudes);

  return (
    latitude >= south &&
    latitude <= north &&
    longitude >= west &&
    longitude <= east
  );
}

function getInterpolatedHoverValues(
  latitude: number,
  longitude: number,
  gridPoints: GridPoint[],
  forecastHour: number
) {
  const gridCoordinates = getGridCoordinates(
    latitude,
    longitude,
    gridPoints
  );

  if (!gridCoordinates) return null;

  const gridX = gridCoordinates.x * (GRID_SIZE - 1);
  const gridY = gridCoordinates.y * (GRID_SIZE - 1);

  const elevationMatrix = buildWeatherMatrix(
    gridPoints,
    forecastHour,
    (point) => point.elevation
  );

  const temperatureMatrix = buildWeatherMatrix(
    gridPoints,
    forecastHour,
    (point, hour) => point.temperature[hour]
  );

  const cloudCoverMatrix = buildWeatherMatrix(
    gridPoints,
    forecastHour,
    (point, hour) => point.cloudCover[hour]
  );

  const precipitationMatrix = buildWeatherMatrix(
    gridPoints,
    forecastHour,
    (point, hour) => point.precipitation[hour]
  );

  const pressureMatrix = buildWeatherMatrix(
    gridPoints,
    forecastHour,
    (point, hour) => point.pressure[hour]
  );

  const windSpeedMatrix = buildWeatherMatrix(
    gridPoints,
    forecastHour,
    (point, hour) => point.windSpeed[hour]
  );

  return {
    elevation: interpolateGridValue(elevationMatrix, gridX, gridY),
    temperature: interpolateGridValue(temperatureMatrix, gridX, gridY),
    cloudCover: interpolateGridValue(cloudCoverMatrix, gridX, gridY),
    precipitation: interpolateGridValue(precipitationMatrix, gridX, gridY),
    pressure: interpolateGridValue(pressureMatrix, gridX, gridY),
    windSpeed: interpolateGridValue(windSpeedMatrix, gridX, gridY),
  };
}

function applyLayerOpacity(
  map: maplibregl.Map,
  selectedLayer: WeatherLayer,
  opacity: number
): void {
  const clampedOpacity = Math.max(0, Math.min(1, opacity));

  if (
    selectedLayer === "temperature" &&
    map.getLayer("temperature-raster-layer")
  ) {
    map.setPaintProperty(
      "temperature-raster-layer",
      "raster-opacity",
      clampedOpacity
    );
  }

  if (
    selectedLayer === "clouds" &&
    map.getLayer("cloud-raster-layer")
  ) {
    map.setPaintProperty(
      "cloud-raster-layer",
      "raster-opacity",
      clampedOpacity
    );
  }

  if (
    selectedLayer === "precipitation" &&
    map.getLayer("precipitation-raster-layer")
  ) {
    map.setPaintProperty(
      "precipitation-raster-layer",
      "raster-opacity",
      clampedOpacity
    );
  }

  if (
    selectedLayer === "elevation" &&
    map.getLayer("elevation-raster-layer")
  ) {
    map.setPaintProperty(
      "elevation-raster-layer",
      "raster-opacity",
      clampedOpacity
    );
  }

  if (
    selectedLayer === "hillshade" &&
    map.getLayer("hillshade-raster-layer")
  ) {
    map.setPaintProperty(
      "hillshade-raster-layer",
      "raster-opacity",
      clampedOpacity
    );
  }

  if (
    selectedLayer === "pressure" &&
    map.getLayer("pressure-layer")
  ) {
    map.setPaintProperty(
      "pressure-layer",
      "circle-opacity",
      clampedOpacity
    );
  }

  if (
    selectedLayer === "wind" &&
    map.getLayer("wind-layer")
  ) {
    map.setPaintProperty(
      "wind-layer",
      "text-opacity",
      clampedOpacity
    );
  }
}

export default function MapView({
  selectedLocation,
  selectedLayer,
  gridPoints,
  forecastHour,
  mapPitch,
  overlayOpacity,
  onLocationSelect,
}: MapViewProps) {
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const gridPointsRef = useRef<GridPoint[]>([]);
  const forecastHourRef = useRef(0);

  useEffect(() => {
    gridPointsRef.current = gridPoints;
  }, [gridPoints]);

  useEffect(() => {
    forecastHourRef.current = forecastHour;
  }, [forecastHour]);

  useEffect(() => {
    if (!mapRef.current) return;

    mapRef.current.setPitch(mapPitch);
  }, [mapPitch]);

  useEffect(() => {
    if (!mapRef.current) return;

    applyLayerOpacity(
      mapRef.current,
      selectedLayer,
      overlayOpacity
    );
  }, [selectedLayer, overlayOpacity]);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [-0.1276, 51.5072],
      zoom: 9,
      pitch: 0,
      bearing: 0,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      if (!map.getSource("terrain-dem")) {
        map.addSource("terrain-dem", {
          type: "raster-dem",
          tiles: [
            "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
          encoding: "terrarium",
          maxzoom: 14,
        });
      }

      map.setTerrain({
        source: "terrain-dem",
        exaggeration: 1.5,
      });
    });

    map.on("click", (event) => {
      onLocationSelect({
        latitude: event.lngLat.lat,
        longitude: event.lngLat.lng,
      });
    });

    map.on("mousemove", (event) => {
      const currentGridPoints = gridPointsRef.current;

      if (
        !isInsideGridBounds(
          event.lngLat.lat,
          event.lngLat.lng,
          currentGridPoints
        )
      ) {
        setHoverInfo(null);
        return;
      }

      const values = getInterpolatedHoverValues(
        event.lngLat.lat,
        event.lngLat.lng,
        currentGridPoints,
        forecastHourRef.current
      );

      if (!values) {
        setHoverInfo(null);
        return;
      }

      setHoverInfo({
        x: event.point.x,
        y: event.point.y,
        ...values,
      });
    });

    map.on("mouseleave", () => {
      setHoverInfo(null);
    });

    mapRef.current = map;

    return () => {
      removeTemperatureLayer(map);
      removeRasterLayer(map);
      removeCloudLayer(map);
      removeCloudRasterLayer(map);
      removePrecipitationLayer(map);
      removePrecipitationRasterLayer(map);
      removeElevationRasterLayer(map);
      removeHillshadeRasterLayer(map);
      removePressureLayer(map);
      removeWindLayer(map);

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

    if (selectedLayer !== "none" && gridPoints.length > 0) {
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
    removeRasterLayer(mapRef.current);
    removeCloudLayer(mapRef.current);
    removeCloudRasterLayer(mapRef.current);
    removePrecipitationLayer(mapRef.current);
    removePrecipitationRasterLayer(mapRef.current);
    removeElevationRasterLayer(mapRef.current);
    removeHillshadeRasterLayer(mapRef.current);
    removePressureLayer(mapRef.current);
    removeWindLayer(mapRef.current);

    if (gridPoints.length === 0) return;

    if (selectedLayer === "temperature") {
      updateRasterLayer(
        mapRef.current,
        gridPoints,
        forecastHour,
        overlayOpacity
      );
    }

    if (selectedLayer === "clouds") {
      updateCloudRasterLayer(
        mapRef.current,
        gridPoints,
        forecastHour,
        overlayOpacity
      );
    }

    if (selectedLayer === "precipitation") {
      updatePrecipitationRasterLayer(
        mapRef.current,
        gridPoints,
        forecastHour,
        overlayOpacity
      );
    }

    if (selectedLayer === "elevation") {
      updateElevationRasterLayer(
        mapRef.current,
        gridPoints,
        overlayOpacity
      );
    }

    if (selectedLayer === "hillshade") {
      updateHillshadeRasterLayer(
        mapRef.current,
        gridPoints,
        overlayOpacity
      );
    }

    if (selectedLayer === "pressure") {
      updatePressureLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }

    if (selectedLayer === "wind") {
      updateWindLayer(
        mapRef.current,
        gridPoints,
        forecastHour
      );
    }

    applyLayerOpacity(
      mapRef.current,
      selectedLayer,
      overlayOpacity
    );
  }, [
    gridPoints,
    selectedLayer,
    forecastHour,
  ]);

  return (
    <div className="map-container-wrapper">
      <div className="map-container" ref={mapContainer} />

      <div className="layer-badge">Layer: {selectedLayer}</div>

      {hoverInfo && (
        <div
          className="map-hover-card"
          style={{
            left: hoverInfo.x + 14,
            top: hoverInfo.y + 14,
          }}
        >
          <p>Elevation: {Math.round(hoverInfo.elevation)} m</p>
          <p>Temp: {hoverInfo.temperature.toFixed(1)} °C</p>
          <p>Cloud: {Math.round(hoverInfo.cloudCover)} %</p>
          <p>Rain: {hoverInfo.precipitation.toFixed(1)} mm</p>
          <p>Pressure: {Math.round(hoverInfo.pressure)} hPa</p>
          <p>Wind: {Math.round(hoverInfo.windSpeed)} km/h</p>
        </div>
      )}
    </div>
  );
}