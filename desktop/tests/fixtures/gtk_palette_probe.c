#include <gtk/gtk.h>
#include <adwaita.h>
#include <stdio.h>

static GtkWidget *button, *entry, *window, *error_label;

static gboolean report(gpointer data) {
    GdkRGBA color, button_color, error_color;
    gtk_style_context_get_color(gtk_widget_get_style_context(GTK_WIDGET(data)), &color);
    gtk_style_context_get_color(gtk_widget_get_style_context(gtk_button_get_child(GTK_BUTTON(button))), &button_color);
    gtk_style_context_get_color(gtk_widget_get_style_context(error_label), &error_color);
    graphene_rect_t bounds = GRAPHENE_RECT_INIT(0, 0, 0, 0);
    int start, end;
    gboolean selection = gtk_editable_get_selection_bounds(GTK_EDITABLE(entry), &start, &end);
    gboolean positioned = gtk_widget_compute_bounds(entry, window, &bounds);
    GtkWidget *focus = gtk_window_get_focus(GTK_WINDOW(window));
    printf("%.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.2f %.2f %.2f %.2f %d %d %d %.6f %.6f %.6f %.6f\n",
           color.red, color.green, color.blue, color.alpha,
           button_color.red, button_color.green, button_color.blue, button_color.alpha,
           bounds.origin.x, bounds.origin.y, bounds.size.width, bounds.size.height,
           selection && start == 0 && end == 12,
           focus && (focus == entry || gtk_widget_is_ancestor(focus, entry)), positioned,
           error_color.red, error_color.green, error_color.blue, error_color.alpha);
    fflush(stdout);
    return G_SOURCE_REMOVE;
}

static void activate(GtkApplication *app, gpointer data) {
    window = adw_application_window_new(app);
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 16);
    GtkWidget *label = gtk_label_new("Tamarack");
    error_label = gtk_label_new("Error");
    gtk_widget_add_css_class(error_label, "error");
    button = gtk_button_new_with_label("Continue");
    entry = gtk_entry_new();
    gtk_editable_set_text(GTK_EDITABLE(entry), "MMMMMMMMMMMM");
    gtk_widget_add_css_class(button, "suggested-action");
    gtk_widget_set_halign(box, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(box, GTK_ALIGN_CENTER);
    gtk_box_append(GTK_BOX(box), label);
    gtk_box_append(GTK_BOX(box), button);
    gtk_box_append(GTK_BOX(box), entry);
    gtk_box_append(GTK_BOX(box), error_label);
    adw_application_window_set_content(ADW_APPLICATION_WINDOW(window), box);
    gtk_window_fullscreen(GTK_WINDOW(window));
    gtk_window_present(GTK_WINDOW(window));
    gtk_widget_grab_focus(entry);
    gtk_editable_select_region(GTK_EDITABLE(entry), 0, -1);
    g_timeout_add(500, report, label);
}

int main(int argc, char **argv) {
    AdwApplication *app = adw_application_new("org.tamlinux.GtkPaletteProbe", G_APPLICATION_NON_UNIQUE);
    g_signal_connect(app, "activate", G_CALLBACK(activate), NULL);
    int status = g_application_run(G_APPLICATION(app), argc, argv);
    g_object_unref(app);
    return status;
}
