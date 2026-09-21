// Non-model, non-game fixture. Access only the explicitly supplied fresh path.
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;

class WriterAccess {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateFile(string name, uint access, uint share,
        IntPtr attrs, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool MoveFileEx(string from, string to, uint flags);
    [DllImport("advapi32.dll", SetLastError=true)]
    static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr output,
        int size, out int needed);

    static void TokenSids(int kind) {
        int size;
        GetTokenInformation(WindowsIdentity.GetCurrent().Token, kind, IntPtr.Zero, 0, out size);
        if (size <= 0 || size > 65536) throw new Exception("token size");
        IntPtr buffer = Marshal.AllocHGlobal(size);
        try {
            if (!GetTokenInformation(WindowsIdentity.GetCurrent().Token, kind, buffer, size, out size))
                throw new Exception("token unavailable");
            int count = Marshal.ReadInt32(buffer);
            if (count < 0 || count > 64) throw new Exception("token count");
            for (int i=0; i<count; i++) {
                IntPtr sid = Marshal.ReadIntPtr(buffer, IntPtr.Size + i * (IntPtr.Size == 8 ? 16 : 8));
                Console.WriteLine("token_" + kind + "=" + new SecurityIdentifier(sid).Value);
            }
        } finally { Marshal.FreeHGlobal(buffer); }
    }

    static int Main(string[] args) {
        if (args.Length != 1 || !System.IO.Path.IsPathRooted(args[0])) return 2;
        Console.WriteLine("user=" + WindowsIdentity.GetCurrent().User.Value);
        TokenSids(11); // TokenRestrictedSids; no credential data.
        bool passed = true;
        foreach (uint access in new uint[]{0x80000000, 0x40000000, 0x10000, 0x40000}) {
            IntPtr file = CreateFile(args[0], access, 7, IntPtr.Zero, 3, 0x80, IntPtr.Zero);
            int error = Marshal.GetLastWin32Error();
            bool ok = file != new IntPtr(-1);
            if (ok) CloseHandle(file);
            Console.WriteLine("access_" + access + "=" + (ok ? 0 : error));
            passed &= access == 0x40000 ? !ok && error == 5 : ok;
        }
        if (!passed) return 4; // Explicit negative access results, not an unhandled I/O exception.
        System.IO.File.WriteAllText(args[0], "synthetic-writer");
        passed &= System.IO.File.ReadAllText(args[0]) == "synthetic-writer";
        bool moved = MoveFileEx(args[0], args[0]+".moved", 0);
        Console.WriteLine("rename=" + (moved ? 0 : Marshal.GetLastWin32Error()));
        if (moved && !MoveFileEx(args[0]+".moved", args[0], 0)) return 3;
        return passed && moved ? 0 : 4;
    }
}
