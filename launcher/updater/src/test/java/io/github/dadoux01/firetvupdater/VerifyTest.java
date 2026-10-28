package io.github.dadoux01.firetvupdater;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class VerifyTest {
    @Test
    public void sha256OfKnownBytes() {
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", Verify.sha256("abc".getBytes()));
    }

    @Test
    public void pinnedCertificateIsASha256() {
        assertTrue(Verify.isSha256(Verify.PROJECT_CERT_SHA256));
        assertFalse(Verify.isSha256("FB0852"));
        assertFalse(Verify.isSha256(null));
    }

    @Test
    public void onlyNewerVersionsAreOffered() {
        assertTrue(Verify.isNewer(12, 11));
        assertTrue(Verify.isNewer(1, -1));
        assertFalse(Verify.isNewer(11, 11));
        assertFalse(Verify.isNewer(10, 11));
    }

    @Test
    public void onlyHttpsGithubAddresses() {
        assertTrue(Verify.trustedUrl("https://github.com/dadoux01/cleanyourtv-firetv/releases/latest/download/update.json"));
        assertTrue(Verify.trustedUrl("https://release-assets.githubusercontent.com/github-production-release-asset/1/x"));
        assertTrue(Verify.trustedUrl("https://objects.githubusercontent.com/x"));
        assertFalse(Verify.trustedUrl("http://github.com/x"));
        assertFalse(Verify.trustedUrl("https://github.com.evil.example/x"));
        assertFalse(Verify.trustedUrl("https://evil.example/https://github.com/x"));
        assertFalse(Verify.trustedUrl(null));
    }

    @Test
    public void fileNamesArePlainApkNames() {
        assertTrue(Verify.safeFileName("cleanyourtv-firetv-launcher.apk"));
        assertFalse(Verify.safeFileName("../x.apk"));
        assertFalse(Verify.safeFileName("a/b.apk"));
        assertFalse(Verify.safeFileName("x.sh"));
    }
}
