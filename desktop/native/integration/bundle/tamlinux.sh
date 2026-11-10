# Native product delivery is initially dormant: retain the existing commands
# first. The cutover transaction explicitly changes environment precedence.
if [ -d /usr/lib/tamlinux/current/bin ]; then
  case ":${PATH:-}:" in
    *:/usr/lib/tamlinux/current/bin:*) ;;
    *) PATH="${PATH:+$PATH:}/usr/lib/tamlinux/current/bin" ;;
  esac
  export PATH
fi
