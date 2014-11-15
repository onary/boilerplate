from webassets import Bundle
# from webassets.filter import get_filter
# sass = get_filter('sass', as_output=True)


sass = Bundle('sass/*.sass', filters='sass', output='gen/sass.css')

common_css = Bundle('css/main.css', sass,
                    filters='yui_css',
                    output='gen/base.css')

bundles = {'css': common_css}
