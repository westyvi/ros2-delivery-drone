#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/opencv.hpp>

class VideoDisplayNode : public rclcpp::Node {
public:
    VideoDisplayNode() : Node("video_display_node") {
        // Create a subscription to the "video_frames" topic with a queue size of 10
        subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
            "processed_frames", 10, std::bind(&VideoDisplayNode::topic_callback, this, std::placeholders::_1)
        );

        // Create an OpenCV window to display the video frames
        cv::namedWindow("Live Video", cv::WINDOW_AUTOSIZE);
    }

    ~VideoDisplayNode() {
        // Destroy the OpenCV window when the node is destroyed
        cv::destroyWindow("Live Video");
    }

private:
    void topic_callback(const sensor_msgs::msg::Image::SharedPtr msg) {
        // Convert the ROS2 Image message to an OpenCV image (cv::Mat) using cv_bridge
        cv::Mat frame = cv_bridge::toCvCopy(msg, "bgr8")->image;

        // Display the image in the OpenCV window
        cv::imshow("Live Video", frame);
        cv::waitKey(1);  // Wait for 1 ms to allow OpenCV to process the window events
    }

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr subscription_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<VideoDisplayNode>());
    rclcpp::shutdown();
    return 0;
}
