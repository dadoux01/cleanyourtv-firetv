package io.github.dadoux01.firetvupdater;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.os.Build;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/** Package checks and the PackageInstaller session. */
final class Installer {
    static final String LAUNCHER = "com.gathin.tvhome";

    private Installer() {}

    /** The installed versionCode of a package, or -1 when it is not installed. */
    static long installedVersion(Context context, String pkg) {
        try {
            PackageInfo info = context.getPackageManager().getPackageInfo(pkg, 0);
            return Build.VERSION.SDK_INT >= 28 ? info.getLongVersionCode() : info.versionCode;
        } catch (PackageManager.NameNotFoundException e) {
            return -1;
        }
    }

    static String installedVersionName(Context context, String pkg) {
        try {
            return context.getPackageManager().getPackageInfo(pkg, 0).versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return null;
        }
    }

    /** SHA-256 of the signing certificate of an installed package, or null. */
    static String installedCert(Context context, String pkg) {
        try {
            return certOf(context.getPackageManager().getPackageInfo(pkg, signingFlag()));
        } catch (PackageManager.NameNotFoundException e) {
            return null;
        }
    }

    /** SHA-256 of the signing certificate of an APK file, or null when it cannot be read. */
    static String archiveCert(Context context, File apk) {
        PackageInfo info = context.getPackageManager().getPackageArchiveInfo(apk.getPath(), signingFlag());
        return info == null ? null : certOf(info);
    }

    static PackageInfo archiveInfo(Context context, File apk) {
        return context.getPackageManager().getPackageArchiveInfo(apk.getPath(), 0);
    }

    @SuppressWarnings("deprecation")
    private static int signingFlag() {
        return Build.VERSION.SDK_INT >= 28 ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES;
    }

    @SuppressWarnings("deprecation")
    private static String certOf(PackageInfo info) {
        Signature[] sigs;
        if (Build.VERSION.SDK_INT >= 28) {
            if (info.signingInfo == null || info.signingInfo.hasMultipleSigners()) return null;
            sigs = info.signingInfo.getSigningCertificateHistory();
            // The current certificate is the last of the history.
            if (sigs == null || sigs.length == 0) return null;
            return Verify.sha256(sigs[sigs.length - 1].toByteArray());
        }
        sigs = info.signatures;
        return sigs == null || sigs.length != 1 ? null : Verify.sha256(sigs[0].toByteArray());
    }

    /** Hands the APK to PackageInstaller; the result arrives in InstallResultReceiver. */
    static void install(Context context, File apk, String pkg) throws IOException {
        PackageInstaller pi = context.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        params.setAppPackageName(pkg);
        int id = pi.createSession(params);
        try (PackageInstaller.Session session = pi.openSession(id)) {
            try (InputStream in = new FileInputStream(apk); OutputStream out = session.openWrite("base.apk", 0, apk.length())) {
                byte[] buf = new byte[1 << 16];
                for (int n; (n = in.read(buf)) > 0; ) out.write(buf, 0, n);
                session.fsync(out);
            }
            Intent result = new Intent(context, InstallResultReceiver.class).putExtra(InstallResultReceiver.EXTRA_TARGET, pkg);
            int flags = PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 31 ? PendingIntent.FLAG_MUTABLE : 0);
            session.commit(PendingIntent.getBroadcast(context, id, result, flags).getIntentSender());
        }
    }
}
