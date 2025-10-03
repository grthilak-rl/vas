# VAS Frontend - Video Aggregation Service

A modern React-based frontend application for the Video Aggregation Service (VAS) - Phase 3.

## 🚀 Features

### Core Features
- **Modern React Application**: Built with React 18, TypeScript, and Material-UI
- **Responsive Design**: Mobile-first responsive UI design system
- **Authentication**: JWT-based authentication with protected routes
- **Real-time Data**: React Query for efficient data fetching and caching

### Device Management
- **Device Dashboard**: Overview of all devices with status indicators
- **Device Listing**: Card-based device display with detailed information
- **Device Operations**: View, edit, and delete device functionality
- **Real-time Status**: Live device status monitoring

### Video Streaming
- **WebRTC Video Player**: Custom video player component for streaming
- **Stream Management**: Start/stop video streams for devices
- **Stream Status**: Real-time stream status monitoring
- **Fullscreen Support**: Fullscreen video playback

### User Interface
- **Material-UI Design**: Modern, accessible UI components
- **Navigation**: Sidebar navigation with active route highlighting
- **Responsive Layout**: Works on desktop, tablet, and mobile devices
- **Loading States**: Proper loading indicators and error handling

## 🛠 Technology Stack

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type-safe JavaScript development
- **Material-UI (MUI)**: React component library for UI design
- **React Router**: Client-side routing
- **React Query (TanStack Query)**: Data fetching and caching
- **Axios**: HTTP client for API communication
- **WebRTC**: Real-time video streaming

## 📦 Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   echo "REACT_APP_API_URL=http://localhost:8000" > .env
   ```

4. **Start the development server:**
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
REACT_APP_NAME=Video Aggregation Service
```

### API Configuration

The frontend connects to the VAS backend API. Make sure the backend is running on the configured URL.

## 🏗 Project Structure

```
frontend/
├── public/                 # Static files
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Layout.tsx     # Main application layout
│   │   └── VideoPlayer.tsx # WebRTC video player
│   ├── contexts/          # React contexts
│   │   └── AuthContext.tsx # Authentication context
│   ├── pages/             # Page components
│   │   ├── Dashboard.tsx  # Main dashboard
│   │   ├── Devices.tsx    # Device management
│   │   ├── Streams.tsx    # Video streaming
│   │   └── Login.tsx      # Authentication
│   ├── services/          # API services
│   │   └── api.ts         # API client
│   ├── types/             # TypeScript type definitions
│   │   └── index.ts       # Shared types
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   ├── App.tsx            # Main application component
│   └── index.tsx          # Application entry point
├── package.json           # Dependencies and scripts
└── tsconfig.json          # TypeScript configuration
```

## 🎯 Usage

### Authentication

1. **Login**: Use the default credentials:
   - Username: `admin`
   - Password: `admin123`

2. **Protected Routes**: All pages except login require authentication

### Dashboard

- **Overview**: View system statistics and health status
- **Device Stats**: See total, online, offline, and unreachable devices
- **Stream Stats**: Monitor active, inactive, and error streams
- **System Health**: Check database and Janus gateway status

### Device Management

- **View Devices**: Browse all discovered devices
- **Device Details**: See device specifications, status, and metadata
- **Device Operations**: Edit or delete devices
- **Status Monitoring**: Real-time device status updates

### Video Streaming

- **Start Streams**: Begin video streaming for online devices
- **Video Player**: Watch live video feeds with controls
- **Stream Management**: Start, stop, and monitor streams
- **Fullscreen Mode**: Fullscreen video playback

## 🔒 Security

- **JWT Authentication**: Secure token-based authentication
- **Protected Routes**: Automatic redirect to login for unauthenticated users
- **API Security**: Secure communication with backend API
- **Role-based Access**: Support for different user roles

## 🚀 Development

### Available Scripts

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Eject from Create React App
npm run eject
```

### Development Guidelines

1. **TypeScript**: Use TypeScript for all new code
2. **Components**: Create reusable, composable components
3. **State Management**: Use React Query for server state, React state for UI state
4. **Styling**: Use Material-UI components and sx prop for custom styling
5. **Error Handling**: Implement proper error boundaries and loading states

## 🔧 Customization

### Theme Customization

Modify the theme in `src/App.tsx`:

```typescript
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});
```

### Component Customization

All components are built with Material-UI and can be customized using:
- `sx` prop for custom styling
- Theme overrides
- Custom component composition

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Error**:
   - Ensure backend is running on correct URL
   - Check CORS configuration in backend
   - Verify environment variables

2. **Authentication Issues**:
   - Clear browser localStorage
   - Check backend authentication endpoints
   - Verify JWT token configuration

3. **Video Streaming Issues**:
   - Ensure Janus gateway is running
   - Check WebRTC browser support
   - Verify device status is ONLINE

### Debug Mode

Enable debug logging by setting:

```env
REACT_APP_DEBUG=true
```

## 📱 Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for all new features
3. Include proper error handling
4. Test on multiple browsers and devices
5. Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the troubleshooting section
2. Review the backend API documentation
3. Open an issue in the repository
