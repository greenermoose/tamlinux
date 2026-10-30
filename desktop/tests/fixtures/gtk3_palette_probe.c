#include <gtk/gtk.h>
#include <stdio.h>

static gboolean report(gpointer data) {
    GdkRGBA color;
    gtk_style_context_get_color(gtk_widget_get_style_context(GTK_WIDGET(data)), GTK_STATE_FLAG_NORMAL, &color);
    printf("%.6f %.6f %.6f %.6f\n", color.red, color.green, color.blue, color.alpha);
    fflush(stdout);
    return G_SOURCE_REMOVE;
}

int main(int argc, char **argv) {
    gtk_init(&argc, &argv);
    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    GtkWidget *label = gtk_label_new("Tamarack");
    gtk_container_add(GTK_CONTAINER(window), label);
    gtk_window_fullscreen(GTK_WINDOW(window));
    gtk_widget_show_all(window);
    g_timeout_add(500, report, label);
    gtk_main();
    return 0;
}
