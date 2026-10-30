#include <gtk/gtk.h>
#include <stdio.h>

static GtkWidget *window, *entry;

static gboolean report(gpointer data) {
    GdkRGBA color;
    int x, y, start, end;
    gtk_style_context_get_color(gtk_widget_get_style_context(GTK_WIDGET(data)), GTK_STATE_FLAG_NORMAL, &color);
    gboolean positioned = gtk_widget_translate_coordinates(entry, window, 0, 0, &x, &y);
    gboolean selected = gtk_editable_get_selection_bounds(GTK_EDITABLE(entry), &start, &end);
    printf("%.6f %.6f %.6f %.6f %d %d %d %d %d %d %d\n", color.red, color.green, color.blue, color.alpha,
           positioned ? x : -1, positioned ? y : -1, gtk_widget_get_allocated_width(entry),
           gtk_widget_get_allocated_height(entry), positioned, gtk_window_get_focus(GTK_WINDOW(window)) == entry,
           selected && start == 0 && end == 12);
    fflush(stdout);
    return G_SOURCE_REMOVE;
}

int main(int argc, char **argv) {
    gtk_init(&argc, &argv);
    window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
    GtkWidget *label = gtk_label_new("Tamarack");
    entry = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(entry), "MMMMMMMMMMMM");
    gtk_widget_set_halign(box, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(box, GTK_ALIGN_CENTER);
    gtk_box_pack_start(GTK_BOX(box), label, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), entry, FALSE, FALSE, 0);
    gtk_container_add(GTK_CONTAINER(window), box);
    gtk_window_fullscreen(GTK_WINDOW(window));
    gtk_widget_show_all(window);
    gtk_widget_grab_focus(entry);
    gtk_editable_select_region(GTK_EDITABLE(entry), 0, -1);
    g_timeout_add(500, report, label);
    gtk_main();
    return 0;
}
