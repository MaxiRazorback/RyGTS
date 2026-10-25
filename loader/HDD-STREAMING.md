# HDD streaming read-ahead

Settings > Graphics > Storage > HDD streaming read-ahead (experimental).
Default: off. Saved as `hdd_streaming=0/1` in `RyGT.ini`. Restart the game after changing it.
The launcher sets `RYGT_HDD_STREAMING=1` or `0` explicitly for the game and device-loss relaunch.
Direct launches may set the environment variable themselves.

Requires the matching libkernel.prx; a launcher-only update cannot change file I/O.
The opt-in Windows implementation supplies `_O_SEQUENTIAL` on read-only /app0/ and /patch0/ opens and APR game-data reads. This requests operating-system sequential read-ahead. It does not reorder guest commands or signal completion early. Writes, save-data paths, direct-I/O opens and directory opens retain their existing behavior. The Windows binary can also be used through Proton; Wine's implementation determines the hint's effect. Native non-Windows builds retain the original path.

This is an initial read-ahead policy, not a general seek scheduler or texture-quality reduction. It adds no private texture cache, background worker, disk-backed memory fallback or whole-archive preload. Windows still manages its normal file cache. Cache hints can increase useful sequential throughput, but random archive access may see no gain or regress. Actual HDD performance has not been measured yet; leave off on SSDs unless comparison proves a benefit.

Validation: launcher and libkernel Release builds; actual kernel positioned and APR reads tested with the option off/on, nonsequential offsets, EOF, short-read tail preservation and missing-file errors. These are correctness checks, not physical HDD throughput measurements.

For measurement use the same game data, track, car count, camera and shader cache, with background disk activity held constant. Compare loading time, on-track hitching and disk latency/queue depth. Account for warm file-cache effects; do not flush the system cache or trim working sets during ordinary play. Test both the first load and repeated visits. Disable the option if random-read hitching worsens.

Microsoft documentation: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew (Caching Behavior).