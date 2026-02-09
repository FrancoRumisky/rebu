import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/auth_service.dart';
import '../../core/config/theme.dart';
import '../trip_create/on_demand_screen.dart';
import '../trip_create/scheduled_screen.dart';
import '../../main.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    final user = authService.user;

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Text('Rebu'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {},
          ),
          IconButton(
            icon: const Icon(Icons.person_outlined),
            onPressed: () => Navigator.pushNamed(context, '/profile'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
  await context.read<AuthService>().logout();
  if (!context.mounted) return;

  Navigator.pushAndRemoveUntil(
    context,
    MaterialPageRoute(builder: (_) => const AuthWrapper()),
    (route) => false,
  );
},
          ),
        ],
      ),
      body: _selectedIndex == 0 ? _homeUberStyle(user) : _buildTripsTab(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Inicio'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'Mis viajes'),
        ],
      ),
    );
  }

  Widget _homeUberStyle(Map<String, dynamic>? user) {
    final name = (user?['full_name'] ?? 'Usuario').toString();

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _header(name),
          const SizedBox(height: 14),
          _whereToCard(),
          const SizedBox(height: 16),
          _quickActions(),
          const SizedBox(height: 18),
          _sectionTitle('Recientes'),
          const SizedBox(height: 10),
          _recentItem(
            title: 'Casa',
            subtitle: 'Agregar dirección',
            icon: Icons.home_outlined,
            onTap: () {},
          ),
          const SizedBox(height: 10),
          _recentItem(
            title: 'Trabajo',
            subtitle: 'Agregar dirección',
            icon: Icons.work_outline,
            onTap: () {},
          ),
          const SizedBox(height: 18),
          _sectionTitle('Cómo funciona'),
          const SizedBox(height: 10),
          _howItWorks(),
        ],
      ),
    );
  }

  Widget _header(String name) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Hola, $name',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: AppTheme.accentColor,
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 4),
        Text(
          '¿Qué tipo de flete necesitás hoy?',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppTheme.mutedTextColor,
              ),
        ),
      ],
    );
  }

  Widget _whereToCard() {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      elevation: 2,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          // En Uber esto abre búsqueda/selección de destino.
          // Podés llevarlo directo a OnDemand por ahora.
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const OnDemandScreen()),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.search, color: AppTheme.primaryColor),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  '¿A dónde vamos?',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: Colors.black87,
                      ),
                ),
              ),
              const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.black38),
            ],
          ),
        ),
      ),
    );
  }

  Widget _quickActions() {
    return Row(
      children: [
        Expanded(
          child: _actionCard(
            title: 'Inmediato',
            subtitle: 'Conductor ahora',
            icon: Icons.flash_on,
            tint: AppTheme.primaryColor,
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const OnDemandScreen()),
              );
            },
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _actionCard(
            title: 'Programado',
            subtitle: 'Para más tarde',
            icon: Icons.schedule,
            tint: AppTheme.accentColor,
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ScheduledScreen()),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _actionCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color tint,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      elevation: 2,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: tint.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: tint),
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: Colors.black87,
                    ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.mutedTextColor,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
            color: AppTheme.accentColor,
          ),
    );
  }

  Widget _recentItem({
    required String title,
    required String subtitle,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      elevation: 1,
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppTheme.primaryColor.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppTheme.primaryColor),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.mutedTextColor,
                          ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.black38),
            ],
          ),
        ),
      ),
    );
  }

  Widget _howItWorks() {
    return Column(
      children: [
        _howTile(
          icon: Icons.location_on_outlined,
          title: 'Indicá origen y destino',
          subtitle: 'Elegí direcciones y detalles del flete.',
        ),
        const SizedBox(height: 10),
        _howTile(
          icon: Icons.local_shipping_outlined,
          title: 'Recibí ofertas',
          subtitle: 'Conductores cercanos te envían propuestas.',
        ),
        const SizedBox(height: 10),
        _howTile(
          icon: Icons.check_circle_outline,
          title: 'Seguimiento',
          subtitle: 'Vas viendo el estado en tiempo real.',
        ),
      ],
    );
  }

  Widget _howTile({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: AppTheme.accentColor.withOpacity(0.10),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: AppTheme.accentColor),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppTheme.mutedTextColor,
                        ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTripsTab() {
    return const Center(
      child: Text('Mis viajes - En construcción'),
    );
  }
}

