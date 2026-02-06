import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/auth_service.dart';
import '../trip_create/on_demand_screen.dart';
import '../trip_create/scheduled_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    final user = authService.user;

    return Scaffold(
    appBar: AppBar(
      automaticallyImplyLeading: false,
      leading: const SizedBox.shrink(), // ✅ mata flecha incluso si algo la intenta meter
      title: const Text('Rebu'),
    actions: [
    IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {
            // Navigate to notifications
            },
          ),
    IconButton(
      icon: const Icon(Icons.person_outlined),
      onPressed: () {
        Navigator.pushNamed(context, '/profile');
      },
    ),
    IconButton(
      icon: const Icon(Icons.logout),
      onPressed: () async {
        await context.read<AuthService>().logout();
        if (!context.mounted) return;
        Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
      },
    ),
  ],
),
      body: _selectedIndex == 0 ? _buildHomeTab(user) : _buildTripsTab(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Inicio',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: 'Mis viajes',
          ),
        ],
      ),
    );
  }

  Widget _buildHomeTab(Map<String, dynamic>? user) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Welcome card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '¡Hola, ${user?['full_name'] ?? 'Usuario'}!',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '¿Qué tipo de flete necesitas?',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            
            // Request type cards
            Text(
              'Tipo de servicio',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 16),
            
            _buildServiceCard(
              context,
              title: 'Flete Inmediato',
              subtitle: 'Encuentra un conductor ahora',
              icon: Icons.flash_on,
              color: Colors.orange,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const OnDemandScreen(),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            
            _buildServiceCard(
              context,
              title: 'Flete Programado',
              subtitle: 'Programa tu flete para más tarde',
              icon: Icons.schedule,
              color: Colors.blue,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const ScheduledScreen(),
                  ),
                );
              },
            ),
            const SizedBox(height: 32),
            
            // Info section
            Text(
              'Cómo funciona',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 16),
            
            _buildInfoTile(
              icon: Icons.location_on,
              title: '1. Indica origen y destino',
              subtitle: 'Dinos dónde recoger y entregar',
            ),
            _buildInfoTile(
              icon: Icons.local_shipping,
              title: '2. Elige tu conductor',
              subtitle: 'Recibe ofertas de conductores cercanos',
            ),
            _buildInfoTile(
              icon: Icons.check_circle,
              title: '3. Completa tu flete',
              subtitle: 'Rastrea tu envío en tiempo real',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServiceCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 4,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  size: 32,
                  color: color,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, size: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoTile({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: Theme.of(context).primaryColor.withOpacity(0.1),
            child: Icon(
              icon,
              color: Theme.of(context).primaryColor,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTripsTab() {
    return const Center(
      child: Text('Mis viajes - En construcción'),
    );
  }
}
