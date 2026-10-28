package io.github.dadoux01.firetvupdater;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Locale;

/** Checks that need no Android API, so plain JVM tests cover them (src/test). */
final class Verify {
    /** SHA-256 of the certificate every published build of the launcher and of this app is signed with. */
    static final String PROJECT_CERT_SHA256 = "fb0852ad1fdc05de1298c11d66fba0f51a789bd3b8a3a204f841434bc9515944";

    private Verify() {}

    static String sha256(byte[] data) {
        try {
            return hex(MessageDigest.getInstance("SHA-256").digest(data));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    static String sha256(File file) throws IOException {
        try (InputStream in = new FileInputStream(file)) {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] buf = new byte[1 << 16];
            for (int n; (n = in.read(buf)) > 0; ) md.update(buf, 0, n);
            return hex(md.digest());
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    static String hex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) sb.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return sb.toString();
    }

    /** A lower-case 64-character hexadecimal SHA-256, as update.json carries them. */
    static boolean isSha256(String s) {
        return s != null && s.matches("[0-9a-f]{64}");
    }

    /** True when a published versionCode is newer than the installed one (-1 when the app is not installed). */
    static boolean isNewer(long published, long installed) {
        return published > installed;
    }

    /** Only HTTPS addresses on GitHub, where the releases live. */
    static boolean trustedUrl(String url) {
        return url != null && url.matches("https://(github\\.com|objects\\.githubusercontent\\.com|release-assets\\.githubusercontent\\.com)/.*");
    }

    /** Asset file names in update.json: plain names, never a path. */
    static boolean safeFileName(String name) {
        return name != null && name.matches("[A-Za-z0-9._-]{1,100}\\.apk");
    }
}
