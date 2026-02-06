import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:provider/provider.dart';
import 'core/config/theme.dart';
import 'core/services/fcm_service.dart';
import 'core/services/auth_service.dart';
import 'features/auth/login_screen.dart';
import 'features/auth/register_screen.dart';
import 'features/home/home_screen.dart';
import 'firebase_options.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
   await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  // Initialize FCM
  await FCMService().initialize();
  
  runApp(const RebuClientApp());
}

class RebuClientApp extends StatelessWidget {
  const RebuClientApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        // Add more providers here
      ],
      child: MaterialApp(
        title: 'Rebu Cliente',
        theme: AppTheme.lightTheme,
        debugShowCheckedModeBanner: false,
        home: const AuthWrapper(),
        routes: {
          '/login': (context) => const LoginScreen(),
          '/home': (context) => const HomeScreen(),
          '/on-demand': (context) => const OnDemandTripScreen(),
          '/scheduled': (context) => const ScheduledTripScreen(),
          '/trip-tracking': (context) => const TripTrackingScreen(),
          '/profile': (context) => const ProfileScreen(),
          '/register': (context) => const RegisterScreen(),
        },
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    
    return authService.isAuthenticated 
        ? const HomeScreen() 
        : const LoginScreen();
  }
}

// Placeholder imports - will be created
class OnDemandTripScreen extends StatelessWidget {
  const OnDemandTripScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('ON_DEMAND')));
}

class ScheduledTripScreen extends StatelessWidget {
  const ScheduledTripScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('SCHEDULED')));
}

class TripTrackingScreen extends StatelessWidget {
  const TripTrackingScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('TRACKING')));
}

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('PROFILE')));
}
