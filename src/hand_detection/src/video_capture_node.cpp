#include <rclcpp/rclcpp.hpp>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/opencv.hpp>

class VideoCaptureNode : public rclcpp::Node {
public:
    VideoCaptureNode() : Node("video_capture_node"), cap_(0) {
        // Check if the camera opened successfully
        if (!cap_.isOpened()) {
            RCLCPP_ERROR(this->get_logger(), "Failed to open camera");
            rclcpp::shutdown();
            return;
        }

        // Create a publisher that will publish Image messages on the "video_frames" topic
        publisher_ = this->create_publisher<sensor_msgs::msg::Image>("video_frames", 10);

        // Create a timer that will call the timer_callback function approximately 30 times per second
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(33),  // ~30 FPS
            std::bind(&VideoCaptureNode::timer_callback, this)
        );
    }

private:
    void timer_callback() {
        cv::Mat frame;
        cap_ >> frame;  // Capture a frame from the webcam
        if (!frame.empty()) {
            // Convert the OpenCV image (cv::Mat) to a ROS2 Image message using cv_bridge
            auto msg = cv_bridge::CvImage(std_msgs::msg::Header(), "bgr8", frame).toImageMsg();

            // Set the timestamp in the message header
            msg->header.stamp = this->now();

            // Publish the Image message
            publisher_->publish(*msg);
        }
    }

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    cv::VideoCapture cap_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<VideoCaptureNode>());
    rclcpp::shutdown();
    return 0;
}
