package io.github.dadoux01.firetvupdater;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * One screen: what is installed, what is published, and a button for each thing to do. Nothing runs in the
 * background: the check happens when the screen opens or the button is pressed.
 */
public class MainActivity extends Activity {
    static final String EXTRA_RESULT_OK = "result_ok";
    static final String EXTRA_RESULT_MESSAGE = "result_message";
    private static final int MAX_MANIFEST = 64 * 1024;
    private static final long MAX_APK = 50L * 1024 * 1024;

    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private TextView installed, latest, status;
    private LinearLayout actions;
    private Release release;
    private boolean busy;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        installed = findViewById(R.id.installed);
        latest = findViewById(R.id.latest);
        status = findViewById(R.id.status);
        actions = findViewById(R.id.actions);
        handleResult(getIntent());
        check();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleResult(intent);
        check();
    }

    @Override
    protected void onResume() {
        super.onResume();
        showInstalled();
        if (release != null) showActions();
    }

    @Override
    protected void onDestroy() {
        worker.shutdownNow();
        super.onDestroy();
    }

    private void handleResult(Intent intent) {
        if (intent == null || !intent.hasExtra(EXTRA_RESULT_OK)) return;
        boolean ok = intent.getBooleanExtra(EXTRA_RESULT_OK, false);
        String msg = intent.getStringExtra(EXTRA_RESULT_MESSAGE);
        status.setText(ok ? getString(R.string.installed_ok) : getString(R.string.install_failed, msg == null ? "?" : msg));
        intent.removeExtra(EXTRA_RESULT_OK);
    }

    private void showInstalled() {
        String name = Installer.installedVersionName(this, Installer.LAUNCHER);
        installed.setText(name == null ? getString(R.string.not_installed) : getString(R.string.installed_version, name));
    }

    private void check() {
        if (busy) return;
        busy = true;
        showInstalled();
        status.setText(R.string.checking);
        worker.execute(() -> {
            try {
                Release r = Release.parse(new String(fetch(Release.MANIFEST_URL, MAX_MANIFEST), "UTF-8"));
                runOnUiThread(() -> {
                    busy = false;
                    release = r;
                    latest.setText(getString(R.string.latest_version, r.tag));
                    status.setText("");
                    showActions();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    busy = false;
                    status.setText(getString(R.string.network_error, String.valueOf(e.getMessage())));
                    showActions();
                });
            }
        });
    }

    /** One button per thing worth doing now; the first one takes the focus for the remote. */
    private void showActions() {
        actions.removeAllViews();
        if (release != null) {
            long have = Installer.installedVersion(this, Installer.LAUNCHER);
            String cert = Installer.installedCert(this, Installer.LAUNCHER);
            if (have >= 0 && !Verify.PROJECT_CERT_SHA256.equals(cert)) {
                status.setText(R.string.other_signature);
                addButton(getString(R.string.uninstall_other), this::uninstallLauncher);
            } else if (have < 0) {
                addButton(getString(R.string.install_launcher), () -> installApp(release.launcher));
            } else if (Verify.isNewer(release.launcher.versionCode, have)) {
                addButton(getString(R.string.update_launcher, release.tag), () -> installApp(release.launcher));
            }
            if (release.updater != null && Verify.isNewer(release.updater.versionCode, Installer.installedVersion(this, getPackageName()))) {
                addButton(getString(R.string.update_self, release.tag), () -> installApp(release.updater));
            }
            if (actions.getChildCount() == 0 && status.getText().length() == 0) status.setText(R.string.up_to_date);
        }
        if (Installer.installedVersion(this, Installer.LAUNCHER) >= 0) {
            addButton(getString(R.string.accessibility), this::openAccessibility);
        }
        addButton(getString(R.string.check), this::check);
        actions.getChildAt(0).requestFocus();
    }

    private void addButton(String label, Runnable action) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(18);
        b.setFocusable(true);
        b.setOnClickListener(v -> {
            if (!busy) action.run();
        });
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.topMargin = (int) (8 * getResources().getDisplayMetrics().density);
        actions.addView(b, lp);
    }

    private void installApp(Release.App app) {
        if (!getPackageManager().canRequestPackageInstalls()) {
            status.setText(R.string.allow_unknown);
            try {
                startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName())));
            } catch (ActivityNotFoundException | SecurityException e) {
                // Fire OS keeps the switch under Developer options: the text above says where.
            }
            return;
        }
        busy = true;
        status.setText(getString(R.string.downloading, app.file));
        String url = release.url(app);
        worker.execute(() -> {
            File apk = new File(getCacheDir(), app.file);
            try {
                download(url, apk);
                runOnUiThread(() -> status.setText(R.string.verifying));
                String problem = check(app, apk);
                if (problem != null) {
                    apk.delete();
                    runOnUiThread(() -> {
                        busy = false;
                        status.setText(getString(R.string.bad_file, problem));
                    });
                    return;
                }
                Installer.install(this, apk, app.packageName);
                runOnUiThread(() -> {
                    busy = false;
                    status.setText(R.string.confirm);
                });
            } catch (Exception e) {
                apk.delete();
                runOnUiThread(() -> {
                    busy = false;
                    status.setText(getString(R.string.network_error, String.valueOf(e.getMessage())));
                });
            }
        });
    }

    /** Why the downloaded APK must not be installed, or null when it is the build update.json describes. */
    private String check(Release.App app, File apk) throws IOException {
        if (!app.sha256.equals(Verify.sha256(apk))) return "SHA-256";
        PackageInfo info = Installer.archiveInfo(this, apk);
        if (info == null) return "APK";
        if (!app.packageName.equals(info.packageName)) return "package " + info.packageName;
        long code = Build.VERSION.SDK_INT >= 28 ? info.getLongVersionCode() : info.versionCode;
        if (code != app.versionCode) return "versionCode " + code;
        // The certificate is pinned in this app, so a release replaced on GitHub (APK and update.json together)
        // is still refused.
        if (!Verify.PROJECT_CERT_SHA256.equals(Installer.archiveCert(this, apk))) return "signature";
        return null;
    }

    private void uninstallLauncher() {
        try {
            startActivity(new Intent(Intent.ACTION_DELETE, Uri.parse("package:" + Installer.LAUNCHER)));
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, R.string.other_signature, Toast.LENGTH_LONG).show();
        }
    }

    private void openAccessibility() {
        try {
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
            Toast.makeText(this, R.string.accessibility_hint, Toast.LENGTH_LONG).show();
        } catch (ActivityNotFoundException e) {
            status.setText(R.string.accessibility_hint);
        }
    }

    // ---- network: HTTPS on GitHub only, size-capped

    private static HttpURLConnection open(String url) throws IOException {
        if (!Verify.trustedUrl(url)) throw new IOException("refused address " + url);
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(30000);
        c.setInstanceFollowRedirects(false);
        c.setRequestProperty("User-Agent", "cleanyourtv-firetv-updater");
        return c;
    }

    /** Follows GitHub's redirects to the release asset by hand, so every hop is checked. */
    private static HttpURLConnection connect(String url) throws IOException {
        for (int hops = 0; hops < 5; hops++) {
            HttpURLConnection c = open(url);
            int code = c.getResponseCode();
            if (code >= 300 && code < 400) {
                String next = c.getHeaderField("Location");
                c.disconnect();
                if (next == null) throw new IOException("redirect without a location");
                url = new URL(new URL(url), next).toString();
                continue;
            }
            if (code != 200) {
                c.disconnect();
                throw new IOException("HTTP " + code);
            }
            return c;
        }
        throw new IOException("too many redirects");
    }

    private static byte[] fetch(String url, int max) throws IOException {
        HttpURLConnection c = connect(url);
        try (InputStream in = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            for (int n; (n = in.read(buf)) > 0; ) {
                out.write(buf, 0, n);
                if (out.size() > max) throw new IOException("answer too large");
            }
            return out.toByteArray();
        } finally {
            c.disconnect();
        }
    }

    private static void download(String url, File dest) throws IOException {
        HttpURLConnection c = connect(url);
        long total = 0;
        try (InputStream in = c.getInputStream(); OutputStream out = new FileOutputStream(dest)) {
            byte[] buf = new byte[1 << 16];
            for (int n; (n = in.read(buf)) > 0; ) {
                total += n;
                if (total > MAX_APK) throw new IOException("file too large");
                out.write(buf, 0, n);
            }
        } finally {
            c.disconnect();
        }
    }
}
