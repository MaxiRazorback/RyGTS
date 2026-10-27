using System.Security.Cryptography;
using GTToolsSharp;
using GTToolsSharp.Encryption;
using GTToolsSharp.Volumes;

/// Finds GT Sport's PS4 shader programs in the game's volumes. Each program ends with a
/// 32-byte footer that starts with "OrbShdr"; the renderer identifies a program by the hash in
/// that footer (offset 16) and the footer gives the code length (bits 8-31 of offset 8).
static class GameShaders
{
    static readonly byte[] Signature = "OrbShdr"u8.ToArray();

    /// (hash, footer offset, code length) of every program in the data.
    public static List<(ulong hash, long footer, int length)> Find(byte[] data)
    {
        var found = new List<(ulong, long, int)>();
        int i = 0;
        while (true)
        {
            int at = data.AsSpan(i).IndexOf(Signature);
            if (at < 0) return found;
            i += at;
            if (i + 32 <= data.Length)
            {
                uint bits = BitConverter.ToUInt32(data, i + 8);
                ulong hash = BitConverter.ToUInt64(data, i + 16);
                found.Add((hash, i, (int)(bits >> 8)));
            }
            i += Signature.Length;
        }
    }

    /// The bytes a program is identified by: its code (up to 64 KB before the footer) and the
    /// footer. The same in every copy of the game.
    public static byte[] ProgramBytes(byte[] data, long footer, int length)
    {
        int len = Math.Clamp(length, 0, 1 << 16);
        long start = Math.Max(0, footer - len);
        long end = Math.Min(data.Length, footer + 32);
        return data[(int)start..(int)end];
    }

    /// Where the program whose footer is at `footer` starts: its first instruction is
    /// s_mov_b32 vcc_hi, imm (0xBEEB03FF) with the footer (imm + 1) * 2 dwords after it, as the
    /// renderer finds the footer. -1 when there is no such instruction.
    public static int CodeStart(byte[] data, long footer)
    {
        for (long p = footer - 8; p >= 0 && footer - p <= (1 << 20); p -= 4)
        {
            if (BitConverter.ToUInt32(data, (int)p) == 0xBEEB03FF &&
                p + ((long)BitConverter.ToUInt32(data, (int)p + 4) + 1) * 8 == footer)
                return (int)p;
        }
        return -1;
    }

    static readonly HashSet<string> SkipExtensions = new(StringComparer.OrdinalIgnoreCase)
    {
        ".JXR", ".JPG", ".PNG", ".MP4", ".SXD", ".SXD2", ".SXD3", ".AST", ".GTESD",
        ".OTF", ".TTF", ".SVG", ".JSON", ".TXT", ".ADC", ".MPROJECT", ".ECP", ".CSS", ".JS",
    };

    /// Walks every file of the volumes (the update's first; a path is read once) and calls
    /// visit(path, bytes) for each file that may hold shaders.
    public static void ForEachFile(IEnumerable<string> indexFiles, string tempDir,
                                   Action<string, byte[]> visit)
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        Directory.CreateDirectory(tempDir);
        string temp = Path.Combine(tempDir, "scan.bin");
        foreach (var index in indexFiles)
        {
            if (!File.Exists(index)) continue;
            GTVolumePFS vol = null;
            foreach (var keyset in KeysetStore.Default_Keysets)
            {
                vol = GTVolumePFS.Load(keyset, index, false, Syroot.BinaryData.Core.Endian.Little);
                if (vol != null) break;
            }
            if (vol == null) continue;
            using (vol)
            {
                var unpacker = new PFSVolumeUnpacker(vol);
                var infos = new Dictionary<uint, GTToolsSharp.BTree.FileInfoKey>();
                foreach (var info in vol.BTree.FileInfos.Entries) infos[info.FileIndex] = info;
                foreach (var file in vol.BTree.GetAllRegisteredFiles())
                {
                    string path = file.Key.Replace('\\', '/');
                    if (!seen.Add(path) || SkipExtensions.Contains(Path.GetExtension(path))) continue;
                    if (File.Exists(temp)) File.Delete(temp);
                    var quiet = Console.Out;
                    Console.SetOut(TextWriter.Null);
                    bool ok;
                    try { ok = unpacker.UnpackFile(infos[file.Value.EntryIndex], path, temp); }
                    finally { Console.SetOut(quiet); }
                    if (!ok || !File.Exists(temp)) continue;
                    visit(path, File.ReadAllBytes(temp));
                }
            }
        }
        if (File.Exists(temp)) File.Delete(temp);
    }

}
