from webassets import Bundle
import settings

sass = Bundle('sass/*.sass',
              filters='sass',
              output='gen/sass.css')

common_css = Bundle('css/*.css', sass,
                    filters='yui_css' if not settings.DEBUG else None,
                    output='gen/base.css')

common_js = Bundle('js/*.js',
                   filters='yui_js' if not settings.DEBUG else None,
                   output='gen/base.js')

bundles = {'css': common_css,
           'js': common_js}
