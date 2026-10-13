-- Layer rules for the Tamlinux shell's surfaces.

-- Keep the bar instant: no layer-shell fade/slide animation.
hl.layer_rule({ match = { namespace = "^tamlinux-bar-.*" }, no_anim = true, animation = "none" })

-- The pickers and the menu pop without compositor layer fades.
hl.layer_rule({ match = { namespace = "^(tamlinux-clipboard|tamlinux-emojis|tamlinux-imagepicker|tamlinux-menu)$" }, no_anim = true, animation = "none" })
