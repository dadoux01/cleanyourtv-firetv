package com.gathin.tvhome;

import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.net.Uri;

/**
 * Management actions for the tile menu and the app library, built from system intents only (the launcher has
 * no INTERNET permission): the Fire TV Appstore's page for an app, where updates are checked, and the
 * system uninstaller. Cache and data are cleared from the App info page, which Fire OS offers for every app.
 * Each method returns null where the TV cannot do it, so the menu leaves the row out.
 */
final class AppActions {
    private AppActions() {}

    /** The Appstore page of the app (amzn://apps/android?p=), where Fire OS shows "Update" when one is out. */
    static Intent update(Context context, String pkg) {
        Intent store = new Intent(Intent.ACTION_VIEW, Uri.parse("amzn://apps/android?p=" + pkg));
        return resolves(context, store) ? store : null;
    }

    /** The system uninstaller, for apps the user installed; null for system apps and for the launcher itself. */
    static Intent uninstall(Context context, String pkg) {
        if (pkg.equals(context.getPackageName())) return null;
        try {
            ApplicationInfo info = context.getPackageManager().getApplicationInfo(pkg, 0);
            if ((info.flags & (ApplicationInfo.FLAG_SYSTEM | ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)) != 0) return null;
        } catch (PackageManager.NameNotFoundException e) {
            return null;
        }
        Intent delete = new Intent(Intent.ACTION_DELETE, Uri.parse("package:" + pkg));
        return resolves(context, delete) ? delete : null;
    }

    private static boolean resolves(Context context, Intent intent) {
        return intent.resolveActivity(context.getPackageManager()) != null;
    }
}
