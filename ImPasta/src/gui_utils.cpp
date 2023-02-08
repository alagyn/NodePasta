#include <gui_utils.h>

#include <iostream>

#include <GLFW/glfw3.h>
#include <backends\imgui_impl_glfw.h>
#include <backends\imgui_impl_opengl3.h>
#include <imnodes.h>

namespace BDD {
    GLFWwindow* window = nullptr;

    const ImVec4 clear_color = ImVec4(0.45f, 0.55f, 0.60f, 1.00f);

    void glfw_error_callback(int error, const char* description)
    {
        std::cout << "GLFW Error " << error << ": " << description;
        exit(1);
    }

    bool gui_init()
    {
        // Setup window
        glfwSetErrorCallback(glfw_error_callback);
        if(!glfwInit())
        {
            std::cout << "Cannot init GLFW\n";
            return false;
        }

        // GL 3.0 + GLSL 130
        const char* glsl_version = "#version 130";
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);

        // Create window with graphics context
        window = glfwCreateWindow(480, 480, "Dear ImGui GLFW+OpenGL3 example", NULL, NULL);
        if(window == NULL)
        {
            std::cout << "Cannot create window\n";
            return false;
        }
        glfwMakeContextCurrent(window);
        glfwSwapInterval(1); // Enable vsync

        // Setup Dear ImGui context
        IMGUI_CHECKVERSION();
        ImGui::CreateContext();
        ImNodes::CreateContext();

        ImGuiIO& io = ImGui::GetIO();

        // Enable Keyboard Controls
        //io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
        // Enable Gamepad Controls
        //io.ConfigFlags |= ImGuiConfigFlags_NavEnableGamepad;

        // Setup Dear ImGui style
        ImGui::StyleColorsDark();

        // Setup Platform/Renderer backends
        ImGui_ImplGlfw_InitForOpenGL(window, true);
        ImGui_ImplOpenGL3_Init(glsl_version);

        ImGui::GetIO().ConfigFlags &= ~ImGuiConfigFlags_NavEnableGamepad;

        return true;
    }

    void gui_stop()
    {
        // Cleanup
        ImGui_ImplGlfw_Shutdown();
        ImNodes::DestroyContext();
        ImGui::DestroyContext();

        glfwDestroyWindow(window);
        glfwTerminate();
        window = nullptr;
    }

    void gui_run(RenderFunc func)
    {
        while(true)
        {
            glfwPollEvents();

            // Start the Dear ImGui frame
            ImGui_ImplOpenGL3_NewFrame();
            ImGui_ImplGlfw_NewFrame();
            ImGui::NewFrame();

            // Rendering
            func();

            ImGui::Render();
            int display_w, display_h;
            glfwGetFramebufferSize(window, &display_w, &display_h);
            glViewport(0, 0, display_w, display_h);
            glClearColor(clear_color.x * clear_color.w,
                         clear_color.y * clear_color.w,
                         clear_color.z * clear_color.w,
                         clear_color.w);
            glClear(GL_COLOR_BUFFER_BIT);
            ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

            glfwSwapBuffers(window);

            if(glfwWindowShouldClose(window))
            {
                break;
            }
        }
    }

} //namespace BDD