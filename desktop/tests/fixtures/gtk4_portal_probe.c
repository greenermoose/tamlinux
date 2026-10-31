#include <adwaita.h>
#include <stdio.h>

static GtkWidget *label;

static gboolean report(gpointer unused) {
    GdkRGBA color;
    gtk_style_context_get_color(gtk_widget_get_style_context(label), &color);
    printf("%.3f %.3f %.3f %.3f\n", color.red, color.green, color.blue, color.alpha);
    fflush(stdout);
    return G_SOURCE_CONTINUE;
}

int main(void) {
    adw_init();
    GtkWidget *window = adw_window_new();
    label = gtk_label_new("Tamarack");
    adw_window_set_content(ADW_WINDOW(window), label);
    gtk_window_present(GTK_WINDOW(window));
    g_timeout_add(500, report, NULL);
    while (1) g_main_context_iteration(NULL, TRUE);
}
