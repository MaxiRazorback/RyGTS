using System;
using System.IO;
using System.Security.Cryptography;
namespace RyGT {
static class GameBuildIntegrity { public static string Hash(string p) { using(var h=SHA256.Create()) using(var f=File.OpenRead(p)) return BitConverter.ToString(h.ComputeHash(f)); } }
class Test { static void Assert(bool b) { if(!b) throw new Exception("assertion failed"); }
static void Main() {
string root=Path.Combine(Path.GetTempPath(),"RyGT-cache-test-"+Guid.NewGuid()); Directory.CreateDirectory(root);
try { string game=Path.Combine(root,"game"), renderer=Path.Combine(root,"renderer"), cache=Path.Combine(root,"shaders"); File.WriteAllText(game,"a"); File.WriteAllText(renderer,"r"); Directory.CreateDirectory(cache);
string shader=Path.Combine(cache,"CUSA03220-direct-sets"); Directory.CreateDirectory(shader); File.WriteAllText(Path.Combine(shader,"stale.spv"),"old"); File.WriteAllText(Path.Combine(cache,"keep.txt"),"keep");
Assert(ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine)); Assert(!Directory.Exists(shader)); Assert(File.Exists(Path.Combine(cache,"keep.txt")));
Directory.CreateDirectory(shader); File.WriteAllText(Path.Combine(shader,"valid.spv"),"valid"); Assert(!ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine)); Assert(File.Exists(Path.Combine(shader,"valid.spv")));
File.WriteAllText(game,"b"); Assert(ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine)); Assert(!Directory.Exists(shader));
Directory.CreateDirectory(shader); File.WriteAllText(renderer,"r2"); Assert(ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine)); Assert(!Directory.Exists(shader));
string old=shader+".outdated"; Directory.CreateDirectory(old); Assert(!ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine)); Assert(!Directory.Exists(old));
Assert(ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine,"amd-uuid"));
Directory.CreateDirectory(shader); File.WriteAllText(Path.Combine(shader,"amd.spv"),"AMD-only instructions");
Assert(!ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine,"amd-uuid")); Assert(Directory.Exists(shader));
Assert(ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine,"nvidia-uuid")); Assert(!Directory.Exists(shader));
Assert(!ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine,"nvidia-uuid"));
Directory.CreateDirectory(shader); File.Delete(renderer); bool failed=false; try { ShaderCacheIdentity.Ensure(cache,game,renderer,Console.WriteLine); } catch(FileNotFoundException) { failed=true; } Assert(failed&&Directory.Exists(shader));
Console.WriteLine("PASS: missing identity, matching identity, game change, renderer change, stale backups, unrelated file preservation, missing binary fail-closed");
} finally { Directory.Delete(root,true); }
} } }
