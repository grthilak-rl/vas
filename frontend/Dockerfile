# Frontend Dockerfile - serves pre-built React app
FROM nginx:alpine

# Copy the built React app to nginx html directory
COPY build/ /usr/share/nginx/html/

# Copy custom nginx configuration if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
