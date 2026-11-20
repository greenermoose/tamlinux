#include <adwaita.h>
#include <stdio.h>

static GtkWidget *label, *window, *view, *suggested, *destructive;

static gboolean report(gpointer unused) {
    GdkRGBA color, suggested_color, destructive_color;
    gtk_style_context_get_color(gtk_widget_get_style_context(label), &color);
    gtk_style_context_get_color(gtk_widget_get_style_context(gtk_button_get_child(GTK_BUTTON(suggested))), &suggested_color);
    gtk_style_context_get_color(gtk_widget_get_style_context(gtk_button_get_child(GTK_BUTTON(destructive))), &destructive_color);
    graphene_rect_t v, s, d;
    gboolean positioned = gtk_widget_compute_bounds(view, window, &v) &&
        gtk_widget_compute_bounds(suggested, window, &s) &&
        gtk_widget_compute_bounds(destructive, window, &d);
    printf("%.3f %.3f %.3f %.3f %d %.0f %.0f %.0f %.0f %.0f %.0f %.0f %.0f %.0f %.0f %.0f %.0f %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.3f\n",
           color.red, color.green, color.blue, color.alpha, positioned,
           v.origin.x, v.origin.y, v.size.width, v.size.height,
           s.origin.x, s.origin.y, s.size.width, s.size.height,
           d.origin.x, d.origin.y, d.size.width, d.size.height,
           suggested_color.red, suggested_color.green, suggested_color.blue, suggested_color.alpha,
           destructive_color.red, destructive_color.green, destructive_color.blue, destructive_color.alpha);
    fflush(stdout);
    return G_SOURCE_CONTINUE;
}

int main(void) {
    adw_init();
    window = adw_window_new();
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    label = gtk_label_new("Tamarack");
    view = gtk_text_view_new();
    gtk_text_buffer_set_text(gtk_text_view_get_buffer(GTK_TEXT_VIEW(view)), "View", -1);
    gtk_widget_set_size_request(view, 130, 40);
    suggested = gtk_button_new_with_label("Continue");
    destructive = gtk_button_new_with_label("Remove");
    gtk_widget_add_css_class(suggested, "suggested-action");
    gtk_widget_add_css_class(destructive, "destructive-action");
    gtk_widget_set_halign(box, GTK_ALIGN_CENTER);
    gtk_widget_set_valign(box, GTK_ALIGN_CENTER);
    gtk_box_append(GTK_BOX(box), label);
    gtk_box_append(GTK_BOX(box), view);
    gtk_box_append(GTK_BOX(box), suggested);
    gtk_box_append(GTK_BOX(box), destructive);
    adw_window_set_content(ADW_WINDOW(window), box);
    gtk_window_fullscreen(GTK_WINDOW(window));
    gtk_window_present(GTK_WINDOW(window));
    g_timeout_add(500, report, NULL);
    while (1) g_main_context_iteration(NULL, TRUE);
}
