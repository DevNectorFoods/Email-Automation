import { useState, useEffect } from "react";
import { X, Info, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { Button } from "./button";

interface NotificationToastProps {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  onDismiss: (id: string) => void;
  autoHide?: boolean;
  duration?: number;
}

const typeIcons = {
  info: Info,
  success: CheckCircle,
  warning: AlertCircle,
  error: XCircle,
};

const typeColors = {
  info: "bg-blue-100 text-blue-600",
  success: "bg-green-100 text-green-600",
  warning: "bg-yellow-100 text-yellow-600",
  error: "bg-red-100 text-red-600",
};

export default function NotificationToast({
  id,
  type,
  title,
  message,
  onDismiss,
  autoHide = true,
  duration = 5000,
}: NotificationToastProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Trigger animation
    setIsVisible(true);

    if (autoHide) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [autoHide, duration]);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => onDismiss(id), 300); // Wait for animation to complete
  };

  const Icon = typeIcons[type];

  return (
    <div
      className={`fixed top-4 right-4 z-50 transform transition-all duration-300 ease-in-out ${
        isVisible ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"
      }`}
    >
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
        <div className="flex items-start space-x-3">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${typeColors[type]}`}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-neutral-800">{title}</p>
            <p className="text-xs text-gray-500 mt-1">{message}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-gray-600 w-6 h-6"
            onClick={handleDismiss}
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export function useNotificationToast() {
  const [notifications, setNotifications] = useState<Array<{
    id: string;
    type: "info" | "success" | "warning" | "error";
    title: string;
    message: string;
  }>>([]);

  const showNotification = (
    type: "info" | "success" | "warning" | "error",
    title: string,
    message: string
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    setNotifications(prev => [...prev, { id, type, title, message }]);
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  const NotificationContainer = () => (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map(notification => (
        <NotificationToast
          key={notification.id}
          {...notification}
          onDismiss={dismissNotification}
        />
      ))}
    </div>
  );

  return {
    showNotification,
    NotificationContainer,
  };
}
