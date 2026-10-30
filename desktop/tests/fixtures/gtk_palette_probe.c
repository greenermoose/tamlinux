#include <gtk/gtk.h>
#include <adwaita.h>
#include <stdio.h>

static GtkWidget *button;

static gboolean report(gpointer data) {
    GdkRGBA color, button_color;
    gtk_style_context_get_color(gtk_widget_get_style_context(GTK_WIDGET(data)), &color);
    gtk_style_context_get_color(gtk_widget_get_style_context(gtk_button_get_child(GTK_BUTTON(button))), &button_color);
    printf("%.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f\n", color.red, color.green, color.blue, color.alpha,
           button_color.red, button_color.green, button_color.blue, button_color.alpha);
    fflush(stdout);
    return G_SOURCE_REMOVE;
}

static void activate(GtkApplication *app, gpointer data) {
    GtkWidget *window = adw_application_window_new(app);
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 16);
    GtkWidget *label = gtk_label_new("Tamarack");
    button = gtk_button_new_with_label("Continue");
    gtk_widget_add_css_class(button, "suggested-action");
    gtk_widget_set_halign(box, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(box, GTK_ALIGN_CENTER);
    gtk_box_append(GTK_BOX(box), label);
    gtk_box_append(GTK_BOX(box), button);
    adw_application_window_set_content(ADW_APPLICATION_WINDOW(window), box);
    gtk_window_fullscreen(GTK_WINDOW(window));
    gtk_window_present(GTK_WINDOW(window));
    g_timeout_add(500, report, label);
}

int main(int argc, char **argv) {
    AdwApplication *app = adw_application_new("org.tamlinux.GtkPaletteProbe", G_APPLICATION_NON_UNIQUE);
    g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);
    int status = g_application_run(G_APPLICATION(app), argc, argv);
    g_object_unref(app);
    return status;
}
