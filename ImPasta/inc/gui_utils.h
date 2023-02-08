#pragma once

#include <boost/function.hpp>

namespace BDD {
    typedef boost::function<void(void)> RenderFunc;
    bool gui_init(void);
    void gui_run(RenderFunc func);
    void gui_stop(void);

} //namespace BDD