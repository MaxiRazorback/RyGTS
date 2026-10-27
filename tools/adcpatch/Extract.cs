using GTToolsSharp;
using GTToolsSharp.Encryption;
using GTToolsSharp.Volumes;

/// Reads files out of GT Sport's volumes (the player's own game folders) with GTToolsSharp.
static class GameFiles
{
    /// Extracts the given volume paths into outputDir (same relative paths). The update's index
    /// is searched first, then the base game's. Returns the paths that were found.
    public static HashSet<string> Extract(IEnumerable<string> indexFiles, IEnumerable<string> paths, string outputDir)
    {
        var wanted = new HashSet<string>(paths.Select(p => p.Replace('\\', '/').ToUpperInvariant()));
        var found = new HashSet<string>();
        foreach (var index in indexFiles)
        {
            if (!File.Exists(index) || found.Count == wanted.Count) continue;
            GTVolumePFS vol = null;
            foreach (var keyset in KeysetStore.Default_Keysets)
            {
                vol = GTVolumePFS.Load(keyset, index, false, Syroot.BinaryData.Core.Endian.Little);
                if (vol != null) break;
            }
            if (vol == null)
            {
                Console.WriteLine($"could not open {index}");
                continue;
            }
            using (vol)
            {
                var unpacker = new PFSVolumeUnpacker(vol);
                var files = vol.BTree.GetAllRegisteredFiles();
                var infos = new Dictionary<uint, GTToolsSharp.BTree.FileInfoKey>();
                foreach (var info in vol.BTree.FileInfos.Entries) infos[info.FileIndex] = info;
                foreach (var file in files)
                {
                    string path = file.Key.Replace('\\', '/');
                    string key = path.ToUpperInvariant();
                    if (!wanted.Contains(key) || found.Contains(key)) continue;
                    string target = Path.Combine(outputDir, key.Replace('/', Path.DirectorySeparatorChar));
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    if (unpacker.UnpackFile(infos[file.Value.EntryIndex], path, target) && File.Exists(target))
                    {
                        found.Add(key);
                        Console.WriteLine($"extracted {key} from {index}");
                    }
                }
            }
        }
        return found;
    }
}
