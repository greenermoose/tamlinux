#include <adwaita.h>
#include <stdio.h>

static GtkWidget *label;
static GMainLoop *loop;

static void print_color(void) {
    GdkRGBA color;
    gtk_style_context_get_color(gtk_widget_get_style_context(label), &color);
    printf("%.6f %.6f %.6f %.6f\n", color.red, color.green, color.blue, color.alpha);
    fflush(stdout);
}

static gboolean set_light(gpointer unused) {
    print_color();
    g_object_set(gtk_settings_get_default(), "gtk-interface-color-scheme",
                 GTK_INTERFACE_COLOR_SCHEME_LIGHT, NULL);
    return G_SOURCE_REMOVE;
}

static gboolean finish(gpointer unused) {
    print_color();
    g_main_loop_quit(loop);
    return G_SOURCE_REMOVE;
}

int main(void) {
    adw_init();
    g_object_set(gtk_settings_get_default(), "gtk-interface-color-scheme",
                 GTK_INTERFACE_COLOR_SCHEME_DARK, NULL);
    GtkWidget *window = adw_window_new();
    label = gtk_label_new("Tamarack");
    adw_window_set_content(ADW_WINDOW(window), label);
    gtk_window_present(GTK_WINDOW(window));
    loop = g_main_loop_new(NULL, FALSE);
    g_timeout_add(500, set_light, NULL);
    g_timeout_add(1500, finish, NULL);
    g_main_loop_run(loop);
    g_main_loop_unref(loop);
    return 0;
}
