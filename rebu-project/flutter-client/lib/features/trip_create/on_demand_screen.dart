import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/config/theme.dart';
import 'viewmodels/on_demand_view_model.dart';

class OnDemandScreen extends StatelessWidget {
  const OnDemandScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => OnDemandViewModel()..init(),
      child: const _OnDemandView(),
    );
  }
}

class _OnDemandView extends StatefulWidget {
  const _OnDemandView();

  @override
  State<_OnDemandView> createState() => _OnDemandViewState();
}

class _OnDemandViewState extends State<_OnDemandView> {
  final pickupCtrl = TextEditingController();
  final dropoffCtrl = TextEditingController();

  @override
  void dispose() {
    pickupCtrl.dispose();
    dropoffCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.watch<OnDemandViewModel>();

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(title: const Text('Flete inmediato')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _whereToHeader(),
            const SizedBox(height: 12),

            _card(
              child: Column(
                children: [
                  _addressField(
                    label: 'Origen',
                    controller: pickupCtrl,
                    icon: Icons.radio_button_checked,
                    iconColor: AppTheme.primaryColor,
                    onSubmitted: (v) => context
                        .read<OnDemandViewModel>()
                        .setPickupFromAddress(v),
                  ),
                  const SizedBox(height: 10),
                  _addressField(
                    label: 'Destino',
                    controller: dropoffCtrl,
                    icon: Icons.location_on,
                    iconColor: AppTheme.accentColor,
                    onSubmitted: (v) => context
                        .read<OnDemandViewModel>()
                        .setDropoffFromAddress(v),
                  ),
                  const SizedBox(height: 12),

                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: vm.isLoading
    ? null
    : () async {
        await context.read<OnDemandViewModel>().useMyLocationAsPickup();
        if (!mounted) return;

        // ✅ set seguro + selección al final
        final text = context.read<OnDemandViewModel>().pickupAddress;
        pickupCtrl.value = TextEditingValue(
          text: text,
          selection: TextSelection.collapsed(offset: text.length),
        );
      },
                          icon: const Icon(Icons.my_location),
                          label: const Text('Usar mi ubicación'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 14),

            if (vm.error != null) ...[
              Text(
                vm.error!,
                style: const TextStyle(color: AppTheme.errorColor),
              ),
              const SizedBox(height: 10),
            ],

            _card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Resumen',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          color: AppTheme.accentColor,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 10),
                  _summaryRow(
                    'Distancia estimada',
                    vm.distanceKm == null
                        ? '—'
                        : '${vm.distanceKm!.toStringAsFixed(1)} km',
                  ),
                  const SizedBox(height: 6),
                  _summaryRow(
                    'Tarifa estimada',
                    vm.estimatedFare == null
                        ? '—'
                        : '\$ ${vm.estimatedFare!.toStringAsFixed(0)}',
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: vm.isLoading
                    ? null
                    : () async {
                        final result =
                            await context.read<OnDemandViewModel>().submit();
                        if (!context.mounted) return;

                        if (result != null) {
                          // MVP: confirmación simple (después lo llevamos a “Buscando conductor…”)
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Solicitud creada ✅'),
                            ),
                          );
                          Navigator.pop(context);
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(vm.error ?? 'Error'),
                              backgroundColor: AppTheme.errorColor,
                            ),
                          );
                        }
                      },
                child: vm.isLoading
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Solicitar flete'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _whereToHeader() {
    return Text(
      '¿A dónde lo llevamos?',
      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: AppTheme.accentColor,
            fontWeight: FontWeight.w800,
          ),
    );
  }

  Widget _card({required Widget child}) {
    return Material(
      color: Colors.white,
      elevation: 2,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: child,
      ),
    );
  }

  Widget _addressField({
    required String label,
    required TextEditingController controller,
    required IconData icon,
    required Color iconColor,
    required ValueChanged<String> onSubmitted,
  }) {
    return TextField(
  controller: controller,
  textInputAction: TextInputAction.search,
  onChanged: (v) {
    // solo guarda texto en memoria (no geocode)
    if (label == 'Origen') {
      context.read<OnDemandViewModel>().pickupAddress = v;
    } else {
      context.read<OnDemandViewModel>().dropoffAddress = v;
    }
  },
  onSubmitted: onSubmitted, // aquí sí geocoding
  decoration: InputDecoration(
    labelText: label,
    prefixIcon: Icon(icon, color: iconColor),
    hintText: 'Escribí una dirección y Enter',
  ),
);
  }

  Widget _summaryRow(String left, String right) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(left, style: const TextStyle(color: AppTheme.mutedTextColor)),
        Text(
          right,
          style: const TextStyle(
            fontWeight: FontWeight.w700,
            color: Colors.black87,
          ),
        ),
      ],
    );
  }
}
