package io.github.dadoux01.firetvupdater;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;

/** Receives PackageInstaller's results: asks the user to confirm, or reports the outcome to the screen. */
public class InstallResultReceiver extends BroadcastReceiver {
    static final String EXTRA_TARGET = "target";

    @Override
    public void onReceive(Context context, Intent intent) {
        int status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        String target = intent.getStringExtra(EXTRA_TARGET);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirm = intent.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirm != null) {
                confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(confirm);
            }
            return;
        }
        boolean ok = status == PackageInstaller.STATUS_SUCCESS;
        if (ok && Installer.LAUNCHER.equals(target)) {
            // Starting the launcher lets it put its Home button service back (restore_key_services): Android switches
            // an app's accessibility services off when the app is replaced.
            Intent launch = context.getPackageManager().getLaunchIntentForPackage(Installer.LAUNCHER);
            if (launch == null) launch = context.getPackageManager().getLeanbackLaunchIntentForPackage(Installer.LAUNCHER);
            if (launch != null) {
                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try {
                    context.startActivity(launch);
                } catch (RuntimeException ignored) {
                    // The result screen below still says it is installed.
                }
            }
        }
        Intent back = new Intent(context, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP)
                .putExtra(MainActivity.EXTRA_RESULT_OK, ok)
                .putExtra(MainActivity.EXTRA_RESULT_MESSAGE, intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE));
        if (!(ok && Installer.LAUNCHER.equals(target))) context.startActivity(back);
    }
}
