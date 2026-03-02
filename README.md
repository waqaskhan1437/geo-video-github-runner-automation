# Geo Video GitHub Runner Automation

Yeh repo ek standalone automation deta hai jo GitHub-hosted runner par:

1. Environment setup karta hai
2. `ffmpeg` + Python dependencies install karta hai
3. Lat/Lon route points se geo-mapping MP4 video banata hai
4. Final video ko GitHub Actions artifact ke taur par upload karta hai

## Files

```text
.github/workflows/geo-video-automation.yml
scripts/geo_video_automation.py
data/route_points.sample.json
requirements.txt
```

## Route Points Format

`data/route_points.sample.json` ya custom JSON input ka format:

```json
{
  "points": [
    { "name": "Karachi", "lat": 24.8607, "lon": 67.0011 },
    { "name": "Dubai", "lat": 25.2048, "lon": 55.2708 }
  ]
}
```

## Run Automation

1. Repo ko GitHub par push karo.
2. `Actions` tab kholo.
3. `Geo Mapping Video Automation` workflow select karo.
4. `Run workflow` pe click karo.
5. Optional inputs do:
   - `points_file` (repo ke andar JSON path)
   - `points_json` (raw JSON; yeh `points_file` ko override karta hai)
   - `title`, `output_name`, `width`, `height`, `fps`, `duration_seconds`
6. Run complete hone ke baad artifact download karo.

## Notes

- Workflow `ubuntu-latest` GitHub-hosted runner use karta hai (fresh instance per run).
- Script world map polygons ke liye open-source GeoJSON fetch karti hai.
- Agar map download fail ho to video phir bhi grid background ke sath ban jati hai.

