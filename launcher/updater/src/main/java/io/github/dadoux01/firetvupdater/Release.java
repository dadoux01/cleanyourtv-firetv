package io.github.dadoux01.firetvupdater;

import org.json.JSONException;
import org.json.JSONObject;

/** The latest release, as described by the update.json the release workflow publishes beside the APKs. */
final class Release {
    static final String REPO = "dadoux01/cleanyourtv-firetv";
    static final String MANIFEST_URL = "https://github.com/" + REPO + "/releases/latest/download/update.json";

    /** One app of the release: the launcher or this updater. */
    static final class App {
        final String packageName;
        final long versionCode;
        final String versionName;
        final String file;
        final String sha256;

        App(String packageName, long versionCode, String versionName, String file, String sha256) {
            this.packageName = packageName;
            this.versionCode = versionCode;
            this.versionName = versionName;
            this.file = file;
            this.sha256 = sha256;
        }
    }

    final String tag;
    final App launcher;
    final App updater;

    private Release(String tag, App launcher, App updater) {
        this.tag = tag;
        this.launcher = launcher;
        this.updater = updater;
    }

    String url(App app) {
        return "https://github.com/" + REPO + "/releases/download/" + tag + "/" + app.file;
    }

    static Release parse(String json) throws JSONException {
        JSONObject root = new JSONObject(json);
        String tag = root.getString("tag");
        if (!tag.matches("v\\d+\\.\\d+\\.\\d+")) throw new JSONException("bad tag " + tag);
        JSONObject apps = root.getJSONObject("apps");
        return new Release(tag, app(apps.getJSONObject("launcher")), apps.has("updater") ? app(apps.getJSONObject("updater")) : null);
    }

    private static App app(JSONObject o) throws JSONException {
        String file = o.getString("file");
        String sha = o.getString("sha256").toLowerCase(java.util.Locale.ROOT);
        if (!Verify.safeFileName(file)) throw new JSONException("bad file name " + file);
        if (!Verify.isSha256(sha)) throw new JSONException("bad sha256 for " + file);
        return new App(o.getString("package"), o.getLong("versionCode"), o.optString("versionName", ""), file, sha);
    }
}
