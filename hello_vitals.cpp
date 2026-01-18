/*
hello_vitals.cpp
Author: Dan Shan
Date: Jan 17, 2026

Description:
Set a pathway to a video file of someone's face to extract and display vitals
*/

#include <smartspectra/container/foreground_container.hpp>
#include <smartspectra/container/settings.hpp>
#include <smartspectra/gui/opencv_hud.hpp>
#include <physiology/modules/messages/metrics.h>
#include <physiology/modules/messages/status.h>
#include <glog/logging.h>
#include <opencv2/opencv.hpp>
#include <iostream>
#include "dotenv.h"

using namespace presage::smartspectra;

int main(int argc, char** argv) {
    // Initialize logging
    google::InitGoogleLogging(argv[0]);
    FLAGS_alsologtostderr = true;

    // Get API key
    std::string api_key;
    if (argc > 1) {
        api_key = argv[1];
    } else api_key = SMARTSPECTRA_API_KEY;
    std::cout << "Starting SmartSpectra Hello Vitals...\n";

    try {
        // Create settings
        container::settings::Settings<
            container::settings::OperationMode::Continuous,
            container::settings::IntegrationMode::Rest
        > settings;

        // Configure camera (defaults work for most cases)

        // settings.video_source.device_index = 0;
        settings.video_source.device_index = -1;
        settings.video_source.input_video_path = "/mnt/d/Download/sample_vid.mp4"; // sample video

        // NOTE: If capture_width and/or capture_height is
        //     modified the HUD will also need to be changed
        settings.video_source.capture_width_px = 1280;
        settings.video_source.capture_height_px = 720;
        settings.video_source.codec = presage::camera::CaptureCodec::MJPG;
        settings.video_source.auto_lock = true;
        // settings.video_source.input_video_path = ""; // paused for testing
        settings.video_source.input_video_time_path = "";

        // Basic settings
        settings.headless = false;
        settings.enable_edge_metrics = true;
        settings.verbosity_level = 1;

        // Continuous mode buffer
        settings.continuous.preprocessed_data_buffer_duration_s = 0.5;

        // API key for REST
        settings.integration.api_key = api_key;

        // Create container
        auto container = std::make_unique<container::CpuContinuousRestForegroundContainer>(settings);
        auto hud = std::make_unique<gui::OpenCvHud>(
            0, 0,
            400,   // width = frame width
            854    // height = frame height
        );

        // Set up callbacks
        // NOTE: If code in callbacks adds more than 75ms of delay it might affect
        //       incoming data.
        auto status = container->SetOnCoreMetricsOutput(
            [&hud](const presage::physiology::MetricsBuffer& metrics, int64_t timestamp) {
                float pulse;
                float breathing;
                if (!metrics.pulse().rate().empty()){
                    std::cout << "Pulse: " << metrics.pulse().rate().rbegin()->value() << " beats / minute\n";
                }
                if (!metrics.breathing().rate().empty()){
                    std::cout << "Breathing: " << metrics.pulse().rate().rbegin()->value() << " breaths / minute\n";
                }
                hud->UpdateWithNewMetrics(metrics);
                return absl::OkStatus();
            }
        );
        if (!status.ok()) {
            std::cerr << "Failed to set metrics callback: " << status.message() << "\n";
            return 1;
        }

        status = container->SetOnVideoOutput(
            [&hud](cv::Mat& frame, int64_t timestamp) {
                if (auto render_status = hud->Render(frame); !render_status.ok()) { // Optional warning
                   // std::cerr << "HUD render failed: " << render_status.message() << "\n";
                }
                // cv::imshow("SmartSpectra Hello Vitals", frame);

                char key = cv::waitKey(1) & 0xFF;
                if (key == 'q' || key == 27) {
                    return absl::CancelledError("User quit");
                }
                return absl::OkStatus();
            }
        );
        if (!status.ok()) {
            std::cerr << "Failed to set video callback: " << status.message() << "\n";
            return 1;
        }
        status = container->SetOnStatusChange(
            [](presage::physiology::StatusValue imaging_status) {
                std::cout << "Imaging/processing status: " << presage::physiology::GetStatusDescription(imaging_status.value()) << "\n";
                return absl::OkStatus();
            }
        );
        if(!status.ok()) {
            std::cerr << "Failed to set status callback: " << status.message() << "\n";
            return 1;
        }
        // Initialize and run
        std::cout << "Initializing camera and processing...\n";
        if (auto status = container->Initialize(); !status.ok()) {
            std::cerr << "Failed to initialize: " << status.message() << "\n";
            return 1;
        }
        std::cout << "Ready! Press 's' to start/stop recording data.\nPress 'q' to quit.\n";
        if (auto status = container->Run(); !status.ok()) {
            std::cerr << "Processing failed: " << status.message() << "\n";
            return 1;
        }
        cv::destroyAllWindows();
        std::cout << "Done!\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
}