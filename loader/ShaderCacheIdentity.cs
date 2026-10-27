using System;
using System.IO;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace RyGT
{
    // Compatibility fingerprint, not publisher authentication.
    static class ShaderCacheIdentity
    {
        static bool Owned(string name)
        {
            return Regex.IsMatch(name, @"^CUSA[0-9]{5}(?:-direct-sets)?(?:\.outdated)?$") ||
                   Regex.IsMatch(name, @"^CUSA[0-9]{5}\.(?:zip|else-scope-fix)$") ||
                   name == "shaders-pack.txt";
        }

        static void CheckTree(string path)
        {
            var attributes = File.GetAttributes(path);
            if ((attributes & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Shader cache cleanup refuses filesystem links: " + path);
            if ((attributes & FileAttributes.Directory) != 0)
                foreach (string child in Directory.GetFileSystemEntries(path)) CheckTree(child);
        }

        public static bool Ensure(string folder, string game, string renderer, Action<string> log)
        {
            // Hash before deleting anything: missing/unreadable binaries abort the launch.
            string identity = "RyGT shader identity 1\n" + GameBuildIntegrity.Hash(game) + "\n" +
                              GameBuildIntegrity.Hash(renderer) + "\n";
            Directory.CreateDirectory(folder);
            if ((File.GetAttributes(folder) & FileAttributes.ReparsePoint) != 0)
                throw new IOException("Shader identity requires the portable cache directory.");
            string stamp = Path.Combine(folder, "cache-identity.sha256");
            bool changed = !File.Exists(stamp) || File.ReadAllText(stamp) != identity;
            var remove = new List<string>();
            foreach (string path in Directory.GetFileSystemEntries(folder))
            {
                string name = Path.GetFileName(path);
                if (Owned(name) && (changed || name.EndsWith(".outdated", StringComparison.Ordinal)))
                    remove.Add(path);
            }
            // Validate all targets before any recursive deletion. Never follow links.
            foreach (string path in remove) CheckTree(path);
            foreach (string path in remove)
            {
                if (Directory.Exists(path)) Directory.Delete(path, true);
                else File.Delete(path);
            }
            // Write only after all cleanup succeeds. A failed cleanup blocks the launch.
            if (changed)
            {
                string temporary = stamp + ".tmp";
                File.WriteAllText(temporary, identity);
                if (File.Exists(stamp)) File.Replace(temporary, stamp, null);
                else File.Move(temporary, stamp);
                log("Game/renderer shader-cache identity changed; incompatible shaders removed for recompilation.");
            }
            return changed;
        }
    }
}
